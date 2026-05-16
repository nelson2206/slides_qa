"""QA orchestrator (provider-agnostic).

Two modes:
- `run_local_qa`: deterministic checks only, NO API calls. Free.
- `run_full_qa`:  deterministic + provider's per-slide + provider's storyline
                  + optional visual analysis.

Providers (Claude or OpenAI) are pluggable via `providers.py`.
The orchestrator never talks to anthropic/openai SDKs directly — it goes
through the Provider interface.

Efficiency knobs:
- Skip non-content slides (cover/divider/minimal) by default
- Configurable workers (default 6)
- Streams `slide_done` events for live UI updates
- Optional visual analysis pass
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterator

from checks import (
    NON_BODY_ROLES,
    classify_action_title_heuristic,
    detect_so_what_heuristic,
    run_deterministic_checks,
)
from providers import Provider, make_provider

# Roles that don't carry analyzable narrative content and are skipped from LLM
# analysis by default. These exist for navigation / boilerplate, not argument:
# - cover / index / divider / closing: structural navigation
# - confidentiality / references / credentials / cv: consulting-deck boilerplate
#   (avisos legales, casos de éxito, credenciales, CVs de consultores)
# - minimal: slides with negligible content
DEFAULT_SKIP_ROLES = frozenset({
    "cover", "index", "divider", "closing", "minimal",
    "confidentiality", "references", "credentials", "cv",
})


# ---------------------------------------------------------------------------
# Severity — map numeric score (0-10) to 4 severity levels.
# ---------------------------------------------------------------------------
#
#   critical (0-4):  multiple structural issues — fix first
#   warning  (5-7):  one clear issue — should fix
#   nit      (8-9):  minor polish — optional
#   ok       (10):   no issues
#
SEVERITY_LABELS = {
    "critical": "Critical",
    "warning":  "Warning",
    "nit":      "Nit",
    "ok":       "OK",
}
SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning":  "🟡",
    "nit":      "🔵",
    "ok":       "🟢",
}
SEVERITY_ORDER = ("critical", "warning", "nit", "ok")


def severity_for(score: int | None) -> str:
    """Map a 0-10 numeric score to a severity level string."""
    if score is None:
        return "nit"          # unknown / skipped → treat as nit
    if score <= 4:
        return "critical"
    if score <= 7:
        return "warning"
    if score <= 9:
        return "nit"
    return "ok"


def _clamp_score(s: Any) -> int:
    """Clamp LLM-returned score to 0..10. Defends against models that
    occasionally return scores outside the 0-10 range despite schema bounds.
    """
    try:
        s = int(s)
    except (TypeError, ValueError):
        return 0
    return max(0, min(10, s))


# ---------------------------------------------------------------------------
# Shared helper — build a per-slide finding from deterministic data only.
# ---------------------------------------------------------------------------

def _build_local_finding(
    slide: dict[str, Any],
    det_slide: dict[str, Any],
    footer_caps: dict[str, Any],
    *,
    skipped: bool = False,
) -> dict[str, Any]:
    n = det_slide["slide_number"]
    paragraphs = det_slide["paragraphs"]
    role = det_slide["role"]
    title = det_slide["title"]
    min_font_size = det_slide.get("min_font_size") or {}
    text_density = det_slide.get("text_density") or {}

    # Local-only heuristics for the semantic checks
    at_h = classify_action_title_heuristic(title)
    sw_h = detect_so_what_heuristic(slide, title)

    score = 10
    issues: list[str] = []
    if not paragraphs["ok"]:
        score -= 2 * min(len(paragraphs["long_paragraphs"]), 2)
        issues.append(f"{len(paragraphs['long_paragraphs'])} párrafo(s) largo(s).")
    if paragraphs["bullet_candidates"]:
        score -= 1
        issues.append("Candidato a bulletear.")
    if role == "content_no_title":
        score -= 3
        issues.append("Slide de contenido sin título.")
    # Heuristic: title is definitely not an action title (1-3 words on a content slide)
    if not skipped and at_h["verdict"] is False and role in ("content_with_title",):
        score -= 2
        issues.append("Título no parece ser un action title.")
    if footer_caps.get("applicable") and not footer_caps.get("ok"):
        outlier_slides = {o["slide_number"] for o in footer_caps.get("outliers", [])}
        if n in outlier_slides:
            score -= 1
            issues.append(
                f"Pie de página en estilo distinto al dominante ({footer_caps['dominant_style']})."
            )
    if not skipped and min_font_size.get("applicable") and not min_font_size.get("ok"):
        score -= 1
        issues.append(min_font_size.get("notes", "Texto bajo el tamaño mínimo."))
    if not skipped and text_density.get("applicable") and not text_density.get("ok"):
        score -= 1
        issues.append(text_density.get("notes", "Slide muy cargada."))
    score = max(0, score)

    skip_note = f" Saltada del análisis semántico (role={role})." if skipped else ""

    return {
        "slide_number": n,
        "role": role,
        "score": score,
        "severity": severity_for(score),
        "summary": (
            ("Análisis local (sin API)." + skip_note + " " + " ".join(issues))
            if issues
            else ("Sin issues estructurales." + skip_note)
        ),
        "_skipped": skipped,
        "action_title": {
            "is_action_title": None if skipped else at_h["verdict"],
            "current_title": title or "",
            "notes": (
                f"Saltada (role={role})." if skipped else at_h["notes"]
            ),
            "suggestion": None if skipped else at_h.get("suggestion"),
        },
        "so_what": {
            "present": None if skipped else sw_h["verdict"],
            "notes": (
                f"Saltada (role={role})." if skipped else sw_h["notes"]
            ),
            "suggestion": None if skipped else sw_h.get("suggestion"),
        },
        "cause_consequence": {
            "ok": None,
            "notes": (
                f"Saltada (role={role})." if skipped
                else "Análisis de causa→consecuencia requiere modo full (con API)."
            ),
        },
        "min_font_size": min_font_size,
        "text_density": text_density,
        "_paragraphs": paragraphs,
        "_footer": det_slide["footer"],
    }


def _build_text_length_block(paragraphs: dict[str, Any]) -> dict[str, Any]:
    n_long = len(paragraphs["long_paragraphs"])
    has_bullet_cand = bool(paragraphs["bullet_candidates"])

    if paragraphs["ok"]:
        suggestion = None
    elif has_bullet_cand and n_long == 1:
        suggestion = (
            "Partí ese párrafo en bullets de 2-3 líneas, o reducilo a la "
            "frase con el insight + 1-2 evidencias."
        )
    elif has_bullet_cand:
        suggestion = (
            f"{n_long} párrafos largos en placeholders de contenido. "
            "Convertilos en bullets cortos (2-3 líneas máx.) o reducí el texto a "
            "la idea clave + evidencia."
        )
    else:
        suggestion = (
            f"Acortá los {n_long} párrafos largos — partilos en bullets de "
            "2-3 líneas, o resumí a la frase con el insight."
        )

    return {
        "ok": paragraphs["ok"],
        "long_paragraphs": [
            f"({lp['shape_name']}, ~{lp['lines_est']} líneas, {lp['word_count']} palabras) "
            f"{lp['snippet']}"
            for lp in paragraphs["long_paragraphs"]
        ],
        "notes": (
            "Sin párrafos largos." if paragraphs["ok"]
            else f"{len(paragraphs['long_paragraphs'])} párrafo(s) exceden el largo recomendado."
        ),
        "suggestion": suggestion,
    }


def _build_footer_block(
    footer: dict[str, Any],
    alignment_ok: bool,
    alignment_notes: str,
    canonical_text: str | None = None,
    role: str | None = None,
    slide_alignment_outlier: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the footer block per slide. Compares against the canonical footer
    text from the deck so the UI can show 'matches canonical' vs 'outlier'.

    `slide_alignment_outlier`, when provided, contains the canonical top/left
    positions and a list of how THIS slide deviates — used to render a concrete
    fix suggestion ("mové el footer a top=X.XX in").

    For non-body roles (cover/index/divider/closing) a missing footer is
    legitimate and gets tagged with exempt=True so the UI can soften wording
    and avoid suggesting "add the canonical footer".
    """
    matches_canonical: bool | None = None
    if footer["present"] and footer.get("text") and canonical_text:
        import re as _re
        def _norm(s: str) -> str:
            return _re.sub(r"\s+", " ", s.strip().lower())
        matches_canonical = _norm(footer["text"]) == _norm(canonical_text)

    exempt = role in NON_BODY_ROLES if role else False

    # Per-slide alignment: True if this slide's footer matches the canonical
    # position (within tolerance). Only False when this slide is in the outlier
    # list — most slides will be aligned even if the deck-level check flagged
    # some inconsistency.
    if not footer["present"]:
        aligned: bool | None = None
    elif slide_alignment_outlier is not None:
        aligned = False
    else:
        aligned = True

    return {
        "present": footer["present"],
        "current_footer": footer.get("text"),
        "aligned": aligned,
        "matches_canonical": matches_canonical,
        "canonical_text": canonical_text,
        "exempt": exempt,
        "alignment_outlier": slide_alignment_outlier,
        "notes": footer["notes"] + (
            "" if not footer["present"] or alignment_ok
            else " " + alignment_notes
        ),
    }


# ---------------------------------------------------------------------------
# LOCAL MODE
# ---------------------------------------------------------------------------

def run_local_qa(file_name: str, deck: dict[str, Any]) -> Iterator[tuple[str, Any]]:
    yield ("status", "Corriendo checks determinísticos (sin API)...")
    det = run_deterministic_checks(file_name, deck)
    footer_caps = det["footer_caps"]
    footer_alignment = det["footer_alignment"]
    canonical_footer = det["footer_text_consistency"].get("dominant_text")

    align_outliers_by_num = {
        o["slide_number"]: o for o in footer_alignment.get("outlier_slides", [])
    }

    slides_report = []
    for slide, det_slide in zip(deck["slides"], det["slides"]):
        # Non-body roles (cover/index/divider/closing) are skipped: no
        # action-title / so-what verdicts, no footer-missing penalty.
        is_non_body = det_slide["role"] in NON_BODY_ROLES
        finding = _build_local_finding(slide, det_slide, footer_caps, skipped=is_non_body)
        finding["text_length"] = _build_text_length_block(finding.pop("_paragraphs"))
        finding["footer"] = _build_footer_block(
            finding.pop("_footer"),
            footer_alignment["ok"],
            footer_alignment.get("notes", ""),
            canonical_text=canonical_footer,
            role=det_slide["role"],
            slide_alignment_outlier=align_outliers_by_num.get(slide["slide_number"]),
        )
        slides_report.append(finding)

    deck_overview = {
        "mode": "local",
        "storyline_coherent": None,
        "storyline_notes": "Análisis de storyline requiere el modo con API.",
        "filename_subtitle_alignment": det["filename_alignment"]["notes"],
        "filename_alignment_detail": det["filename_alignment"],
        "subtitle_filename_alignment_detail": det["subtitle_filename_alignment"],
        "footer_alignment_detail": footer_alignment,
        "footer_caps_detail": footer_caps,
        "footer_text_consistency_detail": det["footer_text_consistency"],
        "footer_matches_deck_title_detail": det["footer_matches_deck_title"],
        "title_format_consistency_detail": det["title_format_consistency"],
        "duplicate_titles_detail": det["duplicate_titles"],
    }

    yield ("result", {"mode": "local", "deck_overview": deck_overview, "slides": slides_report})
    yield ("status", "Análisis local completo.")


# ---------------------------------------------------------------------------
# FULL MODE — delegates to a Provider
# ---------------------------------------------------------------------------

def _merge_finding_with_deterministic(
    finding: dict[str, Any],
    det_slide: dict[str, Any],
    footer_alignment: dict[str, Any],
    canonical_footer: str | None = None,
    slide_alignment_outlier: dict[str, Any] | None = None,
) -> dict[str, Any]:
    paragraphs = det_slide["paragraphs"]
    footer = det_slide["footer"]
    # Clamp the LLM-provided score defensively — schema bounds aren't always
    # enforced strictly, and we never want to show "62/10" in the UI.
    clamped_score = _clamp_score(finding.get("score"))
    return {
        "slide_number": finding["slide_number"],
        "role": det_slide["role"],
        "score": clamped_score,
        "severity": severity_for(clamped_score),
        "summary": finding["summary"],
        "_skipped": finding.get("_skipped", False),
        "action_title": finding["action_title"],
        "so_what": finding["so_what"],
        "cause_consequence": finding["cause_consequence"],
        "text_length": _build_text_length_block(paragraphs),
        "footer": _build_footer_block(
            footer, footer_alignment["ok"], footer_alignment.get("notes", ""),
            canonical_text=canonical_footer,
            role=det_slide["role"],
            slide_alignment_outlier=slide_alignment_outlier,
        ),
        "min_font_size": det_slide.get("min_font_size") or {},
        "text_density": det_slide.get("text_density") or {},
    }


def run_full_qa(
    file_name: str,
    deck: dict[str, Any],
    api_key: str | None = None,
    *,
    provider: str | Provider = "claude",
    max_workers: int = 6,
    skip_roles: set[str] | frozenset[str] | None = None,
    skip_slide_numbers: set[int] | frozenset[int] | None = None,
    visual_analysis: bool = False,
    images_by_slide: dict[int, list[tuple[bytes, str]]] | None = None,
) -> Iterator[tuple[str, Any]]:
    """Full pipeline. Costs tokens.

    Yields:
    - ("status", str)
    - ("slide_done", dict)
    - ("visual_done", dict)
    - ("result", dict)
    - ("error", str)

    Args:
        provider: 'claude' | 'openai' | Provider instance.
        skip_roles: roles to skip from LLM analysis. Default skips divider/minimal.
        skip_slide_numbers: explicit slide numbers to skip (e.g. from a user-deselected section).
        visual_analysis: if True, run vision pass on slides with images.
        images_by_slide: required when visual_analysis=True.
    """
    # Instantiate provider if string given
    if isinstance(provider, str):
        prov = make_provider(provider, api_key=api_key)
    else:
        prov = provider

    skip = frozenset(skip_roles) if skip_roles is not None else DEFAULT_SKIP_ROLES
    skip_nums = frozenset(skip_slide_numbers or ())
    images_by_slide = images_by_slide or {}

    # ----- Stage 1: deterministic -----
    yield ("status", f"1/3 — Checks determinísticos (provider={prov.name})...")
    det = run_deterministic_checks(file_name, deck)
    footer_caps = det["footer_caps"]
    footer_alignment = det["footer_alignment"]

    # Split slides into LLM-analyzed vs deterministic-only
    slides_to_analyze: list[dict[str, Any]] = []
    skipped_findings: dict[int, dict[str, Any]] = {}
    for slide, det_slide in zip(deck["slides"], det["slides"]):
        if det_slide["role"] in skip or slide["slide_number"] in skip_nums:
            placeholder = _build_local_finding(slide, det_slide, footer_caps, skipped=True)
            placeholder.pop("_paragraphs", None)
            placeholder.pop("_footer", None)
            skipped_findings[slide["slide_number"]] = placeholder
        else:
            slides_to_analyze.append(slide)

    if skipped_findings:
        yield (
            "status",
            f"   Skipped {len(skipped_findings)} slide(s) por role: "
            f"{sorted(skipped_findings.keys())} (roles ignorados: {sorted(skip)}).",
        )

    # ----- Stage 2: per-slide analysis (parallel) -----
    total_to_analyze = len(slides_to_analyze)
    if total_to_analyze == 0:
        yield ("status", "2/3 — No hay slides analizables.")
        slide_findings_by_num: dict[int, dict[str, Any]] = {}
    else:
        yield (
            "status",
            f"2/3 — {prov.per_slide_model} analiza {total_to_analyze} slide(s) "
            f"con {max_workers} workers...",
        )
        slide_findings_by_num = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {
                ex.submit(prov.analyze_slide, slide, file_name): slide
                for slide in slides_to_analyze
            }
            completed = 0
            for fut in as_completed(futures):
                slide = futures[fut]
                n = slide["slide_number"]
                try:
                    finding = fut.result()
                except Exception as e:
                    finding = {
                        "slide_number": n,
                        "score": 0,
                        "summary": f"Error en análisis: {e}",
                        "action_title": {"is_action_title": False, "current_title": slide.get("title", ""), "notes": str(e), "suggestion": None},
                        "so_what": {"present": False, "notes": str(e), "suggestion": None},
                        "cause_consequence": {"ok": False, "notes": str(e)},
                        "_error": True,
                    }
                slide_findings_by_num[n] = finding
                completed += 1
                yield (
                    "slide_done",
                    {
                        "slide_number": n,
                        "finding": finding,
                        "completed": completed,
                        "total": total_to_analyze,
                    },
                )

    # ----- Stage 2b: optional visual pass -----
    visual_findings_by_num: dict[int, dict[str, Any]] = {}
    if visual_analysis and images_by_slide:
        slides_with_images = [(n, imgs) for n, imgs in sorted(images_by_slide.items()) if imgs]
        if slides_with_images:
            yield (
                "status",
                f"2b — {prov.visual_model} (visión) analiza "
                f"{len(slides_with_images)} slide(s) con imágenes...",
            )
            slide_by_num = {s["slide_number"]: s for s in deck["slides"]}
            with ThreadPoolExecutor(max_workers=min(max_workers, 4)) as ex:
                futures = {}
                for n, imgs in slides_with_images:
                    slide = slide_by_num.get(n, {})
                    body_text = "\n\n".join(
                        sh["text"] for sh in slide.get("shapes", [])
                        if not sh.get("is_title") and sh.get("text")
                    )
                    fut = ex.submit(
                        prov.analyze_visual, n, imgs, slide.get("title") or "", body_text
                    )
                    futures[fut] = n
                v_completed = 0
                v_total = len(slides_with_images)
                for fut in as_completed(futures):
                    n = futures[fut]
                    try:
                        vfinding = fut.result()
                    except Exception as e:
                        vfinding = {
                            "slide_number": n,
                            "visual_quality": {"ok": False, "notes": f"Error: {e}", "suggestion": None},
                            "chart_readability": {"present": False, "ok": True, "notes": "Error.", "suggestion": None},
                            "design_issues": [str(e)],
                            "_error": True,
                        }
                    visual_findings_by_num[n] = vfinding
                    v_completed += 1
                    yield (
                        "visual_done",
                        {
                            "slide_number": n,
                            "finding": vfinding,
                            "completed": v_completed,
                            "total": v_total,
                        },
                    )

    # ----- Stage 3: storyline -----
    all_findings_in_order: list[dict[str, Any]] = []
    for slide in deck["slides"]:
        n = slide["slide_number"]
        if n in slide_findings_by_num:
            all_findings_in_order.append(slide_findings_by_num[n])
        else:
            all_findings_in_order.append(skipped_findings[n])

    yield ("status", f"3/3 — {prov.storyline_model} evalúa storyline global...")
    try:
        storyline = prov.analyze_storyline(file_name, deck, all_findings_in_order)
    except Exception as e:
        yield ("error", f"Storyline falló: {e}")
        return

    # ----- Merge with deterministic data -----
    canonical_footer = det["footer_text_consistency"].get("dominant_text")
    align_outliers_by_num = {
        o["slide_number"]: o for o in footer_alignment.get("outlier_slides", [])
    }
    slides_merged = []
    for det_slide, slide in zip(det["slides"], deck["slides"]):
        n = slide["slide_number"]
        finding = slide_findings_by_num.get(n) or skipped_findings.get(n)
        merged = _merge_finding_with_deterministic(
            finding, det_slide, footer_alignment, canonical_footer,
            slide_alignment_outlier=align_outliers_by_num.get(n),
        )
        if n in visual_findings_by_num:
            merged["visual"] = visual_findings_by_num[n]
        slides_merged.append(merged)

    # ----- Usage summary (per stage) -----
    per_slide_usage = {
        "input": sum(f.get("_usage", {}).get("input", 0) for f in slide_findings_by_num.values()),
        "output": sum(f.get("_usage", {}).get("output", 0) for f in slide_findings_by_num.values()),
        "cache_read": sum(f.get("_usage", {}).get("cache_read", 0) for f in slide_findings_by_num.values()),
        "cache_write": sum(f.get("_usage", {}).get("cache_write", 0) for f in slide_findings_by_num.values()),
    }
    visual_usage = {
        "input": sum(f.get("_usage", {}).get("input", 0) for f in visual_findings_by_num.values()),
        "output": sum(f.get("_usage", {}).get("output", 0) for f in visual_findings_by_num.values()),
        "cache_read": sum(f.get("_usage", {}).get("cache_read", 0) for f in visual_findings_by_num.values()),
        "cache_write": sum(f.get("_usage", {}).get("cache_write", 0) for f in visual_findings_by_num.values()),
    }
    storyline_usage = storyline.get("_usage", {})

    # ----- Compute actual cost via provider -----
    usage_breakdown = {
        "per_slide": per_slide_usage,
        "storyline": storyline_usage,
        "visual": visual_usage,
    }
    actual_cost = prov.compute_actual_cost(usage_breakdown)

    yield (
        "result",
        {
            "mode": "full",
            "provider": prov.name,
            "models": {
                "per_slide": prov.per_slide_model,
                "storyline": prov.storyline_model,
                "visual": prov.visual_model,
            },
            "deck_overview": {
                "mode": "full",
                "storyline_coherent": storyline["storyline_coherent"],
                "storyline_notes": storyline["storyline_notes"],
                "filename_subtitle_alignment": storyline["filename_subtitle_alignment"],
                "cross_slide_issues": storyline["cross_slide_issues"],
                "filename_alignment_detail": det["filename_alignment"],
                "subtitle_filename_alignment_detail": det["subtitle_filename_alignment"],
                "footer_alignment_detail": footer_alignment,
                "footer_caps_detail": footer_caps,
                "footer_text_consistency_detail": det["footer_text_consistency"],
                "footer_matches_deck_title_detail": det["footer_matches_deck_title"],
                "title_format_consistency_detail": det["title_format_consistency"],
                "duplicate_titles_detail": det["duplicate_titles"],
                "skipped_slides": sorted(skipped_findings.keys()),
                "analyzed_slides": sorted(slide_findings_by_num.keys()),
                "visual_analysis_enabled": visual_analysis,
                "visual_slides": sorted(visual_findings_by_num.keys()),
            },
            "slides": slides_merged,
            "usage": {
                "per_slide": per_slide_usage,
                "storyline": storyline_usage,
                "visual": visual_usage,
            },
            "actual_cost": actual_cost,
        },
    )
    yield ("status", "Análisis completo.")
