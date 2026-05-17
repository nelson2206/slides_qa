"""Deterministic checks that don't need an LLM.

These run locally with no API cost. Coverage:
- Paragraph length (lines, words, chars).
- Footer detection via shape geometry (bottom-left of slide).
- Footer text consistency across slides (should repeat the deck title).
- Footer caps-style consistency.
- Footer matches the deck title from the cover.
- Slide role classification (cover / divider / content with-or-without title).
- Filename <-> slide-title keyword alignment.
- Title format consistency + duplicate title detection.
- Bullet candidates: a single long paragraph in a content placeholder.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Heuristic: body text wraps at roughly this many chars per line in a 12pt body.
# We don't have real font metrics from python-pptx without rendering, so this
# is an estimate. Used to flag paragraphs that LIKELY render as too many lines.
DEFAULT_CHARS_PER_LINE = 80
DEFAULT_MAX_LINES = 3
DEFAULT_MAX_WORDS_PER_PARA = 45


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return text.lower()


def _keywords(text: str, stopwords: set[str] | None = None) -> set[str]:
    stopwords = stopwords or {
        "de", "la", "el", "los", "las", "un", "una", "y", "o", "en", "del",
        "para", "por", "con", "sin", "que", "se", "su", "sus", "al", "a",
        "the", "and", "of", "for", "to", "in", "on", "vs",
    }
    return {w for w in _normalize(text).split() if len(w) > 2 and w not in stopwords}


def estimate_lines(text: str, chars_per_line: int = DEFAULT_CHARS_PER_LINE) -> int:
    """Estimate rendered line count for a paragraph string."""
    if not text:
        return 0
    # Honor explicit line breaks; estimate wrap per segment.
    segments = text.split("\n")
    total = 0
    for seg in segments:
        if not seg:
            total += 1
            continue
        total += max(1, -(-len(seg) // chars_per_line))  # ceil-div
    return total


def check_paragraph(
    paragraph_text: str,
    *,
    max_lines: int = DEFAULT_MAX_LINES,
    max_words: int = DEFAULT_MAX_WORDS_PER_PARA,
    chars_per_line: int = DEFAULT_CHARS_PER_LINE,
) -> dict[str, Any]:
    """Inspect a single paragraph string."""
    word_count = len(paragraph_text.split())
    lines = estimate_lines(paragraph_text, chars_per_line=chars_per_line)
    too_long = lines > max_lines or word_count > max_words
    return {
        "text": paragraph_text,
        "lines_est": lines,
        "word_count": word_count,
        "char_count": len(paragraph_text),
        "too_long": too_long,
    }


def check_slide_paragraphs(slide: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Inspect every paragraph in every non-title shape of a slide.

    Returns {'ok': bool, 'long_paragraphs': [...], 'bullet_candidates': [...]}.
    `bullet_candidates` flags shapes that have ONE long paragraph (likely a
    block of prose that should be broken into bullets).
    """
    long_paragraphs: list[dict[str, Any]] = []
    bullet_candidates: list[dict[str, Any]] = []

    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        paragraphs = shape.get("paragraphs") or []
        if not paragraphs:
            continue

        para_reports = [check_paragraph(p["text"], **kwargs) for p in paragraphs]
        for r in para_reports:
            if r["too_long"]:
                snippet = r["text"][:140] + ("..." if len(r["text"]) > 140 else "")
                long_paragraphs.append(
                    {
                        "shape_name": shape.get("name"),
                        "snippet": snippet,
                        "lines_est": r["lines_est"],
                        "word_count": r["word_count"],
                    }
                )

        if len(paragraphs) == 1 and para_reports[0]["too_long"]:
            bullet_candidates.append(
                {
                    "shape_name": shape.get("name"),
                    "reason": "Una sola párrafo largo en un placeholder: candidato a bulletear.",
                    "snippet": para_reports[0]["text"][:140],
                }
            )

    return {
        "ok": not long_paragraphs,
        "long_paragraphs": long_paragraphs,
        "bullet_candidates": bullet_candidates,
    }


# Minimum readable font size for projector/print decks. MBB standard floor is
# typically 9pt for sources/footnotes; body text usually 11pt+.
DEFAULT_MIN_FONT_PT = 9.0


def check_min_font_size(
    slide: dict[str, Any],
    min_pt: float = DEFAULT_MIN_FONT_PT,
) -> dict[str, Any]:
    """Flag shapes whose explicitly-set font size is below `min_pt`.

    Skips shapes with no explicit size (those inherit from the layout/master
    and are usually safe defaults). Skips the title shape.
    """
    violations: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        size = shape.get("min_font_size_pt")
        if size is None:
            continue
        if size < min_pt - 0.01:  # tolerate float noise
            violations.append({
                "shape_name": shape.get("name"),
                "size_pt": round(size, 1),
                "snippet": (shape.get("text") or "")[:80],
            })

    if not violations:
        return {
            "applicable": True,
            "ok": True,
            "min_required_pt": min_pt,
            "violations": [],
            "notes": f"Todo el texto explícito está ≥ {min_pt:.0f}pt.",
            "suggestion": None,
        }

    smallest = min(v["size_pt"] for v in violations)
    return {
        "applicable": True,
        "ok": False,
        "min_required_pt": min_pt,
        "violations": violations,
        "smallest_pt": smallest,
        "notes": (
            f"{len(violations)} shape(s) con texto < {min_pt:.0f}pt "
            f"(más chico: {smallest:.1f}pt)."
        ),
        "suggestion": (
            f"Subí el tamaño mínimo a {min_pt:.0f}pt — texto bajo ese umbral "
            "es ilegible en proyector y en impresión."
        ),
    }


# Thresholds for "too much text" — when a content slide crosses these, suggest
# splitting, restructuring, or replacing prose with a chart/visual.
# 250 palabras en un slide es aceptable (≈1500-1700 chars en español); flagueamos
# sobre ese piso con buffer. Las dos condiciones se evalúan con OR.
HEAVY_TEXT_WORD_THRESHOLD = 260
HEAVY_TEXT_CHAR_THRESHOLD = 1900


# Approved presentation typeface for the consultancy. ForFuture Sans is the
# brand font (Light / Regular / Medium / Bold / Black + italics). Accept the
# family name in either form and a small set of safe fallbacks the user might
# use when ForFuture isn't available locally.
APPROVED_FONT_FAMILIES = (
    "forfuture sans",
    "forfuture",
)
FALLBACK_FONT_FAMILIES = (
    # System sans that won't break when ForFuture isn't installed.
    "arial",
    "calibri",
    "helvetica",
    "segoe ui",
    "inter",
)


def _normalize_font(name: str) -> str:
    """Lowercase + strip weight/style suffixes so 'ForFutureSans-Bold' matches
    'ForFuture Sans'."""
    if not name:
        return ""
    n = name.lower().strip()
    # Strip common style suffixes/separators
    for suffix in (
        " bold", " black", " medium", " regular", " light", " italic",
        " oblique", " thin", " heavy", " semibold", " extrabold", " extralight",
        "-bold", "-black", "-medium", "-regular", "-light", "-italic",
        "-blackitalic", "-bolditalic", "-mediumitalic", "-lightitalic",
        "-regularitalic",
    ):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    # Normalize 'forfuturesans' / 'forfuture sans' / 'forfuture-sans' → 'forfuture sans'
    n = n.replace("-", " ").replace("_", " ")
    n = " ".join(n.split())
    if n.replace(" ", "") == "forfuturesans":
        return "forfuture sans"
    return n


def check_font_family(slide: dict[str, Any]) -> dict[str, Any]:
    """Check that all explicitly-set fonts are the approved brand typeface
    (ForFuture Sans) or a known safe fallback.

    Shapes/runs without explicit font names are ignored (they inherit from
    layout/master, which should be set correctly at template level).
    """
    seen: dict[str, list[str]] = {}  # normalized → [shape names]
    for shape in slide.get("shapes", []):
        names = shape.get("font_names") or []
        for raw in names:
            norm = _normalize_font(raw)
            if not norm:
                continue
            seen.setdefault(norm, []).append(shape.get("name") or "?")

    if not seen:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Sin fuentes explícitas en runs (heredan del master).",
            "fonts_used": [],
            "approved": list(APPROVED_FONT_FAMILIES),
        }

    approved_set = set(APPROVED_FONT_FAMILIES)
    fallback_set = set(FALLBACK_FONT_FAMILIES)
    non_brand: list[dict[str, Any]] = []
    for norm, shapes_using in seen.items():
        if norm in approved_set:
            continue
        non_brand.append({
            "font": norm,
            "shapes": list(dict.fromkeys(shapes_using))[:5],
            "fallback_ok": norm in fallback_set,
        })

    if not non_brand:
        return {
            "applicable": True,
            "ok": True,
            "notes": f"Todas las fuentes son ForFuture Sans (familia brand).",
            "fonts_used": sorted(seen.keys()),
            "approved": list(APPROVED_FONT_FAMILIES),
            "suggestion": None,
        }

    only_fallbacks = all(v["fallback_ok"] for v in non_brand)
    severity_note = "⚠️ fallback aceptable" if only_fallbacks else "fuera del estándar brand"
    fonts_listed = ", ".join(sorted({v["font"] for v in non_brand}))
    return {
        "applicable": True,
        "ok": False,
        "notes": (
            f"{len(non_brand)} fuente(s) no-brand: {fonts_listed} ({severity_note})."
        ),
        "fonts_used": sorted(seen.keys()),
        "non_brand": non_brand,
        "approved": list(APPROVED_FONT_FAMILIES),
        "only_fallbacks": only_fallbacks,
        "suggestion": (
            "Cambiar las fuentes a ForFuture Sans (la familia brand de la "
            "consultora). Pesos disponibles: Light, Regular, Medium, Bold, "
            "Black (cada uno con italic)."
        ),
    }


def _to_sentence_case(title: str) -> str:
    """Convert a title to sentence case while preserving short ALL-CAPS tokens
    that are usually acronyms (PMO, CV, P&L, Q3, IT, etc.)."""
    words = title.split()
    if not words:
        return title
    out: list[str] = []
    for i, w in enumerate(words):
        # Preserve short ALL-CAPS tokens (acronyms / numbers with letters)
        letters = [c for c in w if c.isalpha()]
        if letters and len(letters) <= 4 and all(c.isupper() for c in letters):
            out.append(w)
            continue
        # First word → upper first letter, lower the rest
        # Subsequent words → all lower (sentence case)
        if i == 0:
            if w and w[0].isalpha():
                out.append(w[0].upper() + w[1:].lower())
            else:
                out.append(w)
        else:
            out.append(w.lower())
    return " ".join(out)


def check_title_not_uppercase(slide: dict[str, Any]) -> dict[str, Any]:
    """Flag titles that violate the consultancy casing convention.

    The standard is **sentence case** (first word + proper nouns capitalized,
    everything else lowercase). Both ALL CAPS and Title Case are flagged.

    - ALL CAPS: ≥95% of alphabetic characters uppercase.
    - Title Case: ≥75% of the 'significant' words (length ≥4 chars to skip
      stopwords like 'el', 'la', 'en', 'de') start with a capital letter.

    Short titles (≤3 alphabetic chars) are skipped to avoid false positives
    on labels like 'P&L' or '2024'.
    """
    title = (slide.get("title") or "").strip()
    if not title:
        return {"applicable": False, "ok": True, "notes": "Sin título."}

    alpha = [c for c in title if c.isalpha()]
    if len(alpha) <= 3:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Título demasiado corto para evaluar mayúsculas.",
            "title": title,
        }

    upper_count = sum(1 for c in alpha if c.isupper())
    pct_upper = upper_count / len(alpha)

    # 1) ALL CAPS
    if pct_upper >= 0.95:
        suggested = _to_sentence_case(title)
        return {
            "applicable": True,
            "ok": False,
            "title": title,
            "pct_upper": round(pct_upper, 2),
            "case_violation": "all_caps",
            "notes": "Título todo en MAYÚSCULAS — la consultora usa sentence case.",
            "suggestion": f'Reescribir en sentence case: "{suggested}".',
        }

    # 2) TITLE CASE — most significant words start uppercase
    words = title.split()
    significant = [
        w for w in words
        if len(w) >= 4 and w[0].isalpha()
    ]
    if len(significant) >= 3:
        cap_count = sum(1 for w in significant if w[0].isupper())
        title_case_ratio = cap_count / len(significant)
        if title_case_ratio >= 0.75:
            suggested = _to_sentence_case(title)
            return {
                "applicable": True,
                "ok": False,
                "title": title,
                "pct_upper": round(pct_upper, 2),
                "title_case_ratio": round(title_case_ratio, 2),
                "case_violation": "title_case",
                "notes": (
                    "Título en Title Case (cada palabra capitalizada) — la "
                    "consultora usa sentence case (solo primera palabra + "
                    "nombres propios)."
                ),
                "suggestion": f'Reescribir en sentence case: "{suggested}".',
            }

    return {
        "applicable": True,
        "ok": True,
        "title": title,
        "pct_upper": round(pct_upper, 2),
        "notes": "Título en sentence case.",
        "suggestion": None,
    }


def check_text_density(slide: dict[str, Any]) -> dict[str, Any]:
    """Flag content slides whose body text density is too high for one page.

    Triggers when total body text exceeds ~120 words or ~800 chars. The
    suggestion encourages adding visuals or restructuring (sub-secciones, charts).
    """
    body_words = 0
    body_chars = 0
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        text = (shape.get("text") or "").strip()
        if not text:
            continue
        body_words += len(text.split())
        body_chars += len(text)

    has_visuals = slide.get("has_visuals", False)

    overloaded = (
        body_words >= HEAVY_TEXT_WORD_THRESHOLD
        or body_chars >= HEAVY_TEXT_CHAR_THRESHOLD
    )

    if not overloaded:
        return {
            "applicable": True,
            "ok": True,
            "word_count": body_words,
            "char_count": body_chars,
            "has_visuals": has_visuals,
            "notes": f"{body_words} palabras · densidad razonable.",
            "suggestion": None,
        }

    if has_visuals:
        suggestion = (
            f"{body_words} palabras en una slide. Considerá dividirla en 2 "
            "(una con el insight + visual, otra con detalle), o convertí el "
            "texto en bullets de 1-2 líneas."
        )
    else:
        suggestion = (
            f"{body_words} palabras de texto sin visuales. Sumá un gráfico, "
            "tabla o esquema que resuma el argumento, y reducí la prosa a "
            "bullets de respaldo. Si no entra, partila en 2 slides."
        )

    return {
        "applicable": True,
        "ok": False,
        "word_count": body_words,
        "char_count": body_chars,
        "has_visuals": has_visuals,
        "notes": (
            f"Slide muy cargada: {body_words} palabras / {body_chars} caracteres."
        ),
        "suggestion": suggestion,
    }


def check_footer(slide: dict[str, Any], slide_height_in: float | None) -> dict[str, Any]:
    """Detect a footer shape (bottom-left of the slide, small height).

    Heuristic:
    - In the bottom 18% of the slide (top_in >= slide_height * 0.82).
    - Height < 0.7 inches (footers are narrow strips).
    - Not the title shape.
    - If multiple qualify, prefer the leftmost one (typical footer position).
    - Ignore tiny purely-numeric shapes (those are page numbers, not footers).
    """
    if slide_height_in is None:
        return {"present": False, "notes": "Sin slide_height_in para evaluar."}

    bottom_threshold = slide_height_in * 0.82

    candidates: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        top = shape.get("top_in")
        height = shape.get("height_in")
        text = (shape.get("text") or "").strip()
        if top is None or height is None or not text:
            continue
        if top < bottom_threshold or height >= 0.7:
            continue
        # Skip page-number-like shapes (very short numeric text)
        if len(text) <= 3 and re.fullmatch(r"[\d/\s\-.]+", text):
            continue
        candidates.append(shape)

    if not candidates:
        return {"present": False, "notes": "No se detectó pie de página."}

    # Prefer leftmost (footers typically sit on the left side)
    candidates.sort(key=lambda s: (s.get("left_in") or 0))
    footer = candidates[0]
    return {
        "present": True,
        "text": footer.get("text"),
        "shape_name": footer.get("name"),
        "top_in": footer.get("top_in"),
        "left_in": footer.get("left_in"),
        "height_in": footer.get("height_in"),
        "notes": "Pie de página detectado en la parte inferior.",
    }


def check_footer_alignment(deck: dict[str, Any]) -> dict[str, Any]:
    """Geometric alignment of footers across slides.

    Flags inconsistent vertical position, horizontal position, or height.
    """
    slide_height_in = deck.get("slide_height_in")
    findings: list[dict[str, Any]] = []
    for slide in deck.get("slides", []):
        footer = check_footer(slide, slide_height_in)
        if footer["present"]:
            findings.append(
                {
                    "slide_number": slide["slide_number"],
                    "top_in": footer["top_in"],
                    "left_in": footer.get("left_in"),
                    "height_in": footer["height_in"],
                    "text": footer["text"],
                }
            )

    if len(findings) < 2:
        return {
            "applicable": len(findings) > 0,
            "ok": True,
            "notes": "Pocas slides con pie de página; no se evalúa alineación.",
            "findings": findings,
        }

    tops = sorted(f["top_in"] for f in findings)
    lefts = sorted(f["left_in"] for f in findings if f["left_in"] is not None)
    heights = sorted(f["height_in"] for f in findings)
    top_range = tops[-1] - tops[0]
    left_range = (lefts[-1] - lefts[0]) if lefts else 0.0
    height_range = heights[-1] - heights[0]

    # Canonical position = median across the deck. Any per-slide footer that
    # deviates from this by more than the tolerance is flagged as an outlier.
    def _median(xs: list[float]) -> float:
        n = len(xs)
        return xs[n // 2] if n % 2 == 1 else (xs[n // 2 - 1] + xs[n // 2]) / 2

    canonical_top = _median(tops)
    canonical_left = _median(lefts) if lefts else None
    canonical_height = _median(heights) if heights else None

    TOP_TOLERANCE = 0.10  # inches — ~7px at 72dpi
    LEFT_TOLERANCE = 0.15

    outlier_slides: list[dict[str, Any]] = []
    for f in findings:
        issues_for_slide: list[str] = []
        if abs(f["top_in"] - canonical_top) > TOP_TOLERANCE:
            issues_for_slide.append(
                f"top={f['top_in']:.2f}in vs canónico {canonical_top:.2f}in"
            )
        if (
            canonical_left is not None
            and f["left_in"] is not None
            and abs(f["left_in"] - canonical_left) > LEFT_TOLERANCE
        ):
            issues_for_slide.append(
                f"left={f['left_in']:.2f}in vs canónico {canonical_left:.2f}in"
            )
        if issues_for_slide:
            outlier_slides.append({
                "slide_number": f["slide_number"],
                "current_top_in": f["top_in"],
                "current_left_in": f["left_in"],
                "canonical_top_in": canonical_top,
                "canonical_left_in": canonical_left,
                "issues": issues_for_slide,
            })

    issues: list[str] = []
    if top_range > 0.15:
        issues.append(f"Footers desalineados verticalmente (rango {top_range:.2f}in).")
    if left_range > 0.25:
        issues.append(f"Footers con horizontal inconsistente (rango {left_range:.2f}in).")
    if height_range > 0.1:
        issues.append(f"Footers con alturas inconsistentes (rango {height_range:.2f}in).")

    return {
        "applicable": True,
        "ok": not issues,
        "notes": " ".join(issues) if issues else "Pies de página visualmente alineados.",
        "findings": findings,
        "top_range_in": top_range,
        "left_range_in": left_range,
        "height_range_in": height_range,
        "canonical_top_in": canonical_top,
        "canonical_left_in": canonical_left,
        "canonical_height_in": canonical_height,
        "outlier_slides": outlier_slides,
    }


def check_footer_text_consistency(deck: dict[str, Any]) -> dict[str, Any]:
    """Most footers should share the SAME text (the deck title repeated).

    Flags decks where footers vary across slides (different strings, or some
    slides have footers and others don't).
    """
    from collections import Counter

    slide_height_in = deck.get("slide_height_in")
    content_slides = 0
    footers: list[dict[str, Any]] = []
    for slide in deck.get("slides", []):
        role = classify_slide_role(slide)
        if role in ("content_with_title", "content_no_title"):
            content_slides += 1
        footer = check_footer(slide, slide_height_in)
        if footer["present"] and footer.get("text"):
            footers.append(
                {"slide_number": slide["slide_number"], "text": footer["text"], "role": role}
            )

    if not footers:
        return {
            "applicable": content_slides > 0,
            "ok": content_slides == 0,
            "notes": (
                "Ninguna slide tiene pie de página."
                if content_slides > 0
                else "Sin slides de contenido para evaluar."
            ),
            "total_footers": 0,
            "content_slides": content_slides,
            "coverage_pct": 0.0,
        }

    # Coverage: % of content slides that have a footer
    content_with_footer = sum(
        1 for f in footers if f["role"] in ("content_with_title", "content_no_title")
    )
    coverage_pct = content_with_footer / max(1, content_slides)

    # Text consistency: group by normalized text
    normalized = [_normalize(f["text"]).strip() for f in footers]
    counts = Counter(normalized)
    dominant_norm, dominant_count = counts.most_common(1)[0]
    dominant_example = next(
        f["text"] for f, n in zip(footers, normalized) if n == dominant_norm
    )

    consistency_pct = dominant_count / len(footers)
    distinct_variants = len(counts)

    issues: list[str] = []
    if coverage_pct < 0.6 and content_slides >= 3:
        issues.append(
            f"Cobertura baja: solo {content_with_footer}/{content_slides} slides "
            f"de contenido ({coverage_pct:.0%}) tienen footer."
        )
    if consistency_pct < 0.7:
        issues.append(
            f"{distinct_variants} variantes de texto en {len(footers)} footers — debería ser una sola."
        )

    return {
        "applicable": True,
        "ok": not issues,
        "total_footers": len(footers),
        "content_slides": content_slides,
        "content_with_footer": content_with_footer,
        "coverage_pct": coverage_pct,
        "distinct_variants": distinct_variants,
        "dominant_text": dominant_example,
        "dominant_count": dominant_count,
        "consistency_pct": consistency_pct,
        "variations": [
            {"text": next(f["text"] for f, n in zip(footers, normalized) if n == k), "count": v}
            for k, v in counts.most_common()
        ],
        "notes": (
            " ".join(issues)
            if issues
            else f"{dominant_count}/{len(footers)} footers usan el mismo texto: \"{dominant_example}\"."
        ),
    }


def check_footer_matches_deck_title(deck: dict[str, Any]) -> dict[str, Any]:
    """The footer should repeat the deck title (or at least share keywords with it)."""
    slides = deck.get("slides", [])
    if not slides:
        return {"applicable": False, "ok": True, "notes": "Sin slides."}

    cover_title = (slides[0].get("title") or "").strip()
    if not cover_title:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Portada sin título; no se puede comparar con el footer.",
        }

    cover_kw = _keywords(cover_title)
    if not cover_kw:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Título de portada sin keywords útiles (solo stopwords).",
        }

    slide_height_in = deck.get("slide_height_in")
    matches: list[dict[str, Any]] = []
    total_footers = 0
    for slide in slides:
        footer = check_footer(slide, slide_height_in)
        if footer["present"] and footer.get("text"):
            total_footers += 1
            footer_kw = _keywords(footer["text"])
            overlap = cover_kw & footer_kw
            if overlap:
                matches.append(
                    {
                        "slide_number": slide["slide_number"],
                        "shared": sorted(overlap),
                        "text": footer["text"],
                    }
                )

    if total_footers == 0:
        return {
            "applicable": False,
            "ok": True,
            "notes": "No hay footers en el deck para comparar.",
            "cover_title": cover_title,
        }

    coverage = len(matches) / total_footers
    ok = coverage >= 0.5
    return {
        "applicable": True,
        "ok": ok,
        "cover_title": cover_title,
        "cover_keywords": sorted(cover_kw),
        "matching_slides": [m["slide_number"] for m in matches],
        "total_footers": total_footers,
        "match_count": len(matches),
        "coverage_pct": coverage,
        "notes": (
            f"{len(matches)}/{total_footers} footer(s) comparten keywords con el título de la portada "
            f'("{cover_title[:60]}{"..." if len(cover_title) > 60 else ""}").'
            if ok
            else f"Solo {len(matches)}/{total_footers} footer(s) repiten algo del título de la portada — "
                 f"el pie de página debería usar el título del deck."
        ),
    }


# ---------------------------------------------------------------------------
# Local heuristics for action title and so-what (no LLM)
# ---------------------------------------------------------------------------

# Spanish conclusion / implication markers — if any appear in the body, the
# so-what is probably stated (or at least signposted) in text.
SO_WHAT_MARKERS = (
    "por lo tanto",
    "en consecuencia",
    "esto implica",
    "esto demuestra",
    "esto significa",
    "implica que",
    "lo que sugiere",
    "se traduce en",
    "como resultado",
    "por consiguiente",
    "conclusión:",
    "implicancia:",
    "implicación:",
    "recomendación:",
    "decisión:",
)


def classify_action_title_heuristic(title: str | None) -> dict[str, Any]:
    """Local-only judgment of whether a title is an action title.

    Heuristic: action titles are full statements with subject+verb+conclusion,
    usually 7+ words. 1-3 word titles are descriptive labels. 4-6 is borderline.

    Returns:
        dict with `verdict` (True/False/None), `notes`, `suggestion`.
    """
    if not title or not title.strip():
        return {
            "verdict": False,
            "notes": "Sin título — todo slide de contenido debería tener un action title.",
            "suggestion": "Agregar un action title con sujeto + verbo + conclusión con insight.",
        }

    words = title.strip().split()
    n = len(words)

    if n <= 3:
        return {
            "verdict": False,
            "notes": (
                f"Solo {n} palabra(s) — es una etiqueta descriptiva, "
                f"no una afirmación con insight."
            ),
            "suggestion": (
                f"Convertir en action title (sujeto + verbo + conclusión). "
                f"En vez de \"{title}\", algo como: "
                f"\"Los X principales sobre {title.lower()} son ...\" o "
                f"\"{title} muestra que ...\"."
            ),
        }

    if n <= 6:
        return {
            "verdict": None,
            "notes": (
                f"{n} palabras — borderline. Puede ser action title si tiene "
                f"verbo y conclusión clara, o solo una frase descriptiva."
            ),
            "suggestion": (
                "Verificar manualmente: ¿se entiende la conclusión leyendo "
                "solo el título? Si no, expandir a 8+ palabras con el insight."
            ),
        }

    return {
        "verdict": True,
        "notes": f"{n} palabras — formato típico de action title.",
        "suggestion": None,
    }


def detect_so_what_heuristic(
    slide: dict[str, Any],
    title: str | None,
) -> dict[str, Any]:
    """Local-only judgment of whether the so-what is present.

    Two paths to "present":
    1. Title is a likely action title (the so-what lives IN the title).
    2. Body text contains explicit conclusion markers ("por lo tanto", etc.).
    """
    # Path 1: action title carries the so-what
    if title:
        at = classify_action_title_heuristic(title)
        if at["verdict"] is True:
            return {
                "verdict": True,
                "notes": "El título tiene formato de action title — el so-what está ahí.",
                "suggestion": None,
            }

    # Path 2: look for explicit conclusion markers in the body
    body_text = " ".join(
        sh.get("text", "")
        for sh in slide.get("shapes", [])
        if not sh.get("is_title") and sh.get("text")
    )
    if not body_text.strip():
        return {
            "verdict": None,
            "notes": "Sin cuerpo de texto para analizar.",
            "suggestion": None,
        }

    body_lower = body_text.lower()
    found = [m for m in SO_WHAT_MARKERS if m in body_lower]
    if found:
        return {
            "verdict": True,
            "notes": (
                f"Marcador de conclusión detectado en el cuerpo: \"{found[0]}\"."
            ),
            "suggestion": None,
        }

    return {
        "verdict": None,
        "notes": (
            "No se detectaron marcadores explícitos de conclusión y el título "
            "no tiene formato de action title. Posiblemente falta el so-what."
        ),
        "suggestion": (
            "Hacer visible la conclusión: o bien en el título, o bien como una "
            "caja destacada en la slide (ej: \"Implicancia: ...\")."
        ),
    }


# ---------------------------------------------------------------------------
# Caps-style consistency of footers
# ---------------------------------------------------------------------------

_ANTE_TITLE_PREFIX_RE = re.compile(r"^\s*\d+\.\s*")


def classify_caps(text: str) -> str:
    """Classify casing style: 'all_upper', 'title_case', 'lower', 'mixed', 'empty'.

    Strips a leading "NN. " section prefix before classifying — we care about
    the section name's style, not the numeric prefix.
    """
    if not text:
        return "empty"
    stripped = _ANTE_TITLE_PREFIX_RE.sub("", text).strip()
    if not stripped:
        return "empty"

    letters = [c for c in stripped if c.isalpha()]
    if len(letters) < 3:
        return "mixed"

    upper_count = sum(1 for c in letters if c.isupper())
    upper_ratio = upper_count / len(letters)

    if upper_ratio >= 0.85:
        return "all_upper"
    # First letter capitalized, rest mostly lowercase → title case.
    # Check this BEFORE the `lower` branch — words like "Contexto" have a low
    # uppercase ratio (1/8) but should still be title_case.
    if stripped[0].isalpha() and stripped[0].isupper() and upper_ratio < 0.3:
        return "title_case"
    if upper_ratio < 0.1:
        return "lower"
    return "mixed"


def check_footer_caps_consistency(deck: dict[str, Any]) -> dict[str, Any]:
    """Across slides with footers, verify caps style is consistent.

    All footer text should use the same casing convention (title case OR
    all caps OR sentence case). Mixed styles signal editorial drift.
    """
    slide_height_in = deck.get("slide_height_in")
    findings: list[dict[str, Any]] = []
    for slide in deck.get("slides", []):
        footer = check_footer(slide, slide_height_in)
        if footer["present"] and footer.get("text"):
            findings.append(
                {
                    "slide_number": slide["slide_number"],
                    "text": footer["text"],
                    "style": classify_caps(footer["text"]),
                }
            )

    if len(findings) < 2:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Pocas slides con pie de página; no se evalúa caps.",
            "findings": findings,
        }

    style_counts: dict[str, int] = {}
    for f in findings:
        style_counts[f["style"]] = style_counts.get(f["style"], 0) + 1

    distinct = [s for s, c in style_counts.items() if c >= 1 and s != "empty"]
    dominant = max(style_counts, key=lambda s: style_counts[s])
    outliers = [f for f in findings if f["style"] != dominant]

    ok = len(distinct) <= 1
    return {
        "applicable": True,
        "ok": ok,
        "style_counts": style_counts,
        "dominant_style": dominant,
        "outliers": outliers,
        "findings": findings,
        "notes": (
            f"Estilo dominante: {dominant} ({style_counts[dominant]} slides)."
            if ok
            else (
                f"Mezcla de estilos en footers: {style_counts}. "
                f"Outliers vs dominante ({dominant}): "
                f"{[o['slide_number'] for o in outliers]}."
            )
        ),
    }


# ---------------------------------------------------------------------------
# Slide role classifier (cover / divider / content)
# ---------------------------------------------------------------------------

_DIVIDER_LAYOUT_HINTS = ("section", "divider", "title only", "cover")

# Roles whose footer is legitimately absent — these slides don't need a footer,
# and a missing one should not be flagged. Also skipped from LLM analysis by default.
NON_BODY_ROLES = frozenset({
    "cover", "index", "divider", "closing",
    "confidentiality", "references", "credentials", "cv",
})

# Index/agenda title keywords (case- and accent-insensitive substring match)
_INDEX_TITLE_KEYWORDS = (
    "agenda", "indice", "contenido", "contenidos",
    "tabla de contenido", "tabla de contenidos",
    "table of contents", "contents", "outline",
)

# Closing-slide title keywords
_CLOSING_TITLE_KEYWORDS = (
    "gracias", "muchas gracias", "thank you", "thanks",
    "preguntas", "questions", "q&a", "q & a", "q and a",
    "contacto", "contactos", "contact",
    "the end",
)

# Boilerplate slide keywords — common in consulting decks (Minsait/MBB style).
# Each maps to a NON_BODY_ROLE so the slide is skipped from semantic analysis.
_CONFIDENTIALITY_TITLE_KEYWORDS = (
    "confidencialidad", "aviso de confidencialidad", "aviso legal",
    "disclaimer", "confidential notice", "confidentiality",
)
_REFERENCES_TITLE_KEYWORDS = (
    "referencias", "clientes y referencias", "casos de exito", "casos de éxito",
    "case studies", "casos de referencia", "nuestros clientes",
)
_CREDENTIALS_TITLE_KEYWORDS = (
    "credenciales", "credentials", "nuestras credenciales",
)
_CV_TITLE_KEYWORDS = (
    "cv", "cvs",  # short keywords matched as standalone words
    "curriculum",
    "consultores asignados", "perfil del equipo", "perfiles del equipo",
    "equipo asignado",
)

# Common section-divider titles in consulting decks. When a slide's title
# EXACTLY (post-normalization) matches one of these, we classify it as a
# divider regardless of layout — these are always structural separators.
_SECTION_DIVIDER_EXACT_TITLES = (
    "contexto y objetivos",
    "contexto",
    "objetivos",
    "nuestro enfoque",
    "enfoque",
    "valor anadido y aceleradores minsait",
    "valor anadido y aceleradores",
    "valor anadido",
    "aceleradores minsait",
    "aceleradores",
    "metodologia de trabajo",
    "metodologia",
    "plan de trabajo",
    "plan",
    "equipo de trabajo",
    "equipo",
    "nuestro equipo",
)


_TOC_NUMBER_PREFIX_RE = re.compile(
    r"^\s*(?:\d{1,2}|[IVX]{1,4})\s*[\.\)\-–—:]?\s*\S"
)


def _looks_like_toc(slide: dict[str, Any]) -> bool:
    """Heuristic: this slide is structurally a table of contents.

    Looks for ≥3 short text items (or paragraphs within text shapes) that
    start with a numbered prefix (1., 01, I., etc.). Catches the case where
    the deck has an index/TOC slide whose title isn't 'Agenda'/'Índice' but
    whose body lists 'Capítulo 01 — Introducción', '02 Análisis', etc.
    """
    numbered_items = 0
    short_items = 0
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        text = (shape.get("text") or "").strip()
        if not text:
            continue
        for line in text.split("\n"):
            line = line.strip()
            if not line or len(line) > 120:
                continue
            short_items += 1
            if _TOC_NUMBER_PREFIX_RE.match(line):
                numbered_items += 1
    return numbered_items >= 3


def _title_has_any_keyword(title_norm: str, keywords: tuple[str, ...]) -> bool:
    """Check if a normalized title contains any of the given keywords.

    Short keywords (≤3 chars, like 'cv') match only as standalone words to
    avoid false positives ('mcv', 'cvs' substring matches). Longer keywords
    match as substrings.
    """
    if not title_norm:
        return False
    words = title_norm.split()
    for kw in keywords:
        if len(kw) <= 3:
            if kw in words:
                return True
        elif kw in title_norm:
            return True
    return False


def _normalize_title_for_match(text: str) -> str:
    """Lowercase + strip accents for fuzzy keyword matching."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accents.lower().strip()


def classify_slide_role(slide: dict[str, Any], *, total_slides: int | None = None) -> str:
    """Return one of: 'cover', 'index', 'divider', 'closing',
    'content_with_title', 'content_no_title', 'minimal'.

    Roles in `NON_BODY_ROLES` (cover, index, divider, closing) legitimately
    have no body footer and are skipped from semantic analysis by default.
    """
    slide_n = slide.get("slide_number", 0)
    layout = (slide.get("layout_name") or "").lower()
    title = (slide.get("title") or "").strip()
    title_norm = _normalize_title_for_match(title)
    has_title = bool(title)

    if slide_n == 1:
        return "cover"

    # Divider/section-header LAYOUT takes precedence — these are the chapter
    # boundaries used by sections.detect_sections, regardless of whether the
    # title contains 'Referencias' or 'Contexto'. Their content is also skipped.
    if any(hint in layout for hint in _DIVIDER_LAYOUT_HINTS):
        return "divider"

    # Exact title match against known consulting-deck section names → also
    # treat as a divider (even on a regular layout), as long as the body
    # is reasonable (< 200 chars). Catches "Nuestro enfoque" / "Contexto y
    # objetivos" / "Equipo de trabajo" / etc. slides that are structurally
    # separators but didn't use the Section Header layout.
    if has_title and title_norm in _SECTION_DIVIDER_EXACT_TITLES:
        body_chars_quick = sum(
            len((sh.get("text") or "").strip())
            for sh in slide.get("shapes", [])
            if not sh.get("is_title")
        )
        if body_chars_quick < 200:
            return "divider"

    # Boilerplate slides common in consulting decks — skipped from analysis.
    if has_title and _title_has_any_keyword(title_norm, _CONFIDENTIALITY_TITLE_KEYWORDS):
        return "confidentiality"

    # Index / agenda — keyword match in title (typically early in the deck).
    if has_title and _title_has_any_keyword(title_norm, _INDEX_TITLE_KEYWORDS):
        return "index"

    # Structural index detection — a slide between positions 2-4 whose body
    # is a numbered list of chapters/sections is a TOC, even if the title
    # doesn't say 'Agenda' or 'Índice'.
    if 2 <= slide_n <= 4 and _looks_like_toc(slide):
        return "index"

    if has_title and _title_has_any_keyword(title_norm, _REFERENCES_TITLE_KEYWORDS):
        return "references"

    if has_title and _title_has_any_keyword(title_norm, _CREDENTIALS_TITLE_KEYWORDS):
        return "credentials"

    if has_title and _title_has_any_keyword(title_norm, _CV_TITLE_KEYWORDS):
        return "cv"

    # Closing slide — keyword match in title (typically at the end).
    if has_title and _title_has_any_keyword(title_norm, _CLOSING_TITLE_KEYWORDS):
        return "closing"

    body_chars = 0
    body_shapes_with_text = 0
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        text = (shape.get("text") or "").strip()
        if text:
            body_chars += len(text)
            body_shapes_with_text += 1

    # Big chunk of body text or several text shapes → it's a content slide.
    if body_chars > 150 or body_shapes_with_text >= 3:
        return "content_with_title" if has_title else "content_no_title"

    # Has a title and only a tiny body → probably a section/divider-ish slide.
    if has_title and body_chars < 80:
        # If this is the last slide and has barely any body, treat as closing
        # (covers cases where the user named it "Final" / "" / something custom).
        if total_slides is not None and slide_n == total_slides and body_chars < 40:
            return "closing"
        return "divider"

    return "minimal"


def check_filename_alignment(deck: dict[str, Any], file_name: str) -> dict[str, Any]:
    """Check if filename keywords appear in slide titles or subtitles."""
    base = re.sub(r"\.pptx$", "", file_name, flags=re.IGNORECASE)
    base = re.sub(r"[_\-]+", " ", base)
    name_kw = _keywords(base)

    if not name_kw:
        return {"applicable": False, "ok": True, "notes": "Nombre de archivo sin keywords útiles."}

    matches: list[dict[str, Any]] = []
    misses: list[int] = []
    for slide in deck.get("slides", []):
        title = slide.get("title") or ""
        if not title:
            continue
        title_kw = _keywords(title)
        overlap = name_kw & title_kw
        if overlap:
            matches.append({"slide_number": slide["slide_number"], "shared": sorted(overlap)})

    cover_aligned = any(m["slide_number"] == 1 for m in matches)
    return {
        "applicable": True,
        "ok": cover_aligned or len(matches) >= 2,
        "filename_keywords": sorted(name_kw),
        "matches": matches,
        "cover_aligned": cover_aligned,
        "notes": (
            f"Coincidencias con nombre de archivo en {len(matches)} slide(s)."
            + ("" if cover_aligned else " La portada no comparte keywords con el filename.")
        ),
    }


# ---------------------------------------------------------------------------
# Subtitle-specific filename alignment
# ---------------------------------------------------------------------------

def _extract_subtitles(deck: dict[str, Any]) -> list[dict[str, Any]]:
    """Find SUBTITLE-type placeholders across the deck."""
    subtitles: list[dict[str, Any]] = []
    for slide in deck.get("slides", []):
        for shape in slide.get("shapes", []):
            ptype = (shape.get("placeholder_type") or "").upper()
            if "SUBTITLE" in ptype:
                text = (shape.get("text") or "").strip()
                if text:
                    subtitles.append(
                        {"slide_number": slide["slide_number"], "text": text}
                    )
    return subtitles


def check_subtitle_filename_alignment(deck: dict[str, Any], file_name: str) -> dict[str, Any]:
    """Specifically check SUBTITLE placeholders against filename keywords.

    This is the literal interpretation of the original ask "los subtítulos sean
    iguales al nombre del archivo" — separate from the broader title-overlap
    check, because subtitles are the editorial vehicle for "what is this deck".
    """
    base = re.sub(r"\.pptx$", "", file_name, flags=re.IGNORECASE)
    base = re.sub(r"[_\-]+", " ", base)
    name_kw = _keywords(base)

    if not name_kw:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Nombre de archivo sin keywords útiles.",
            "subtitles": [],
        }

    subtitles = _extract_subtitles(deck)
    if not subtitles:
        return {
            "applicable": False,
            "ok": True,
            "notes": "No se detectaron placeholders de tipo SUBTITLE.",
            "subtitles": [],
        }

    matches: list[dict[str, Any]] = []
    for sub in subtitles:
        sub_kw = _keywords(sub["text"])
        overlap = name_kw & sub_kw
        if overlap:
            matches.append(
                {
                    "slide_number": sub["slide_number"],
                    "shared": sorted(overlap),
                    "text": sub["text"],
                }
            )

    return {
        "applicable": True,
        "ok": len(matches) >= 1,
        "filename_keywords": sorted(name_kw),
        "subtitles_found": len(subtitles),
        "subtitles": subtitles,
        "matches": matches,
        "notes": (
            f"{len(matches)}/{len(subtitles)} subtítulo(s) comparte(n) keywords con el filename."
            if matches
            else f"Encontrados {len(subtitles)} subtítulo(s); ninguno comparte keywords con el filename ({sorted(name_kw)})."
        ),
    }


# ---------------------------------------------------------------------------
# Title format consistency (short labels vs long action sentences)
# ---------------------------------------------------------------------------

def classify_title_length(title: str | None) -> str:
    """Bucket a title by word count: 'empty', 'short', 'medium', 'long'."""
    if not title or not title.strip():
        return "empty"
    n_words = len(title.strip().split())
    if n_words <= 3:
        return "short"
    if n_words <= 7:
        return "medium"
    return "long"


def check_title_format_consistency(deck: dict[str, Any]) -> dict[str, Any]:
    """Flag decks that mix very short labels with long action sentences.

    The mix itself is the issue (editorial inconsistency) — not whether any
    individual title is "good". A deck where most titles are 1-3 word labels
    but a few are 8+ word sentences signals two different authors/styles.
    """
    buckets: dict[str, list[int]] = {"empty": [], "short": [], "medium": [], "long": []}
    for slide in deck.get("slides", []):
        b = classify_title_length(slide.get("title"))
        buckets[b].append(slide["slide_number"])

    total_with_title = sum(len(v) for k, v in buckets.items() if k != "empty")
    if total_with_title < 4:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Pocos títulos para evaluar consistencia.",
            "counts": {k: len(v) for k, v in buckets.items()},
            "buckets": buckets,
        }

    short_pct = len(buckets["short"]) / total_with_title
    long_pct = len(buckets["long"]) / total_with_title
    inconsistent = short_pct >= 0.2 and long_pct >= 0.2

    return {
        "applicable": True,
        "ok": not inconsistent,
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
        "notes": (
            f"Mezcla de estilos de título: {len(buckets['short'])} corto(s) "
            f"({short_pct:.0%}) + {len(buckets['long'])} largo(s) ({long_pct:.0%}) "
            f"sobre {total_with_title} con título. Outliers cortos: {buckets['short'][:5]}{'...' if len(buckets['short']) > 5 else ''}; "
            f"largos: {buckets['long'][:5]}{'...' if len(buckets['long']) > 5 else ''}."
            if inconsistent
            else f"Formato de títulos consistente (predominante: "
                 f"{max((k for k in ['short','medium','long']), key=lambda k: len(buckets[k]))})."
        ),
    }


# ---------------------------------------------------------------------------
# Duplicate slide titles
# ---------------------------------------------------------------------------

def check_duplicate_titles(deck: dict[str, Any]) -> dict[str, Any]:
    """Find slides whose title text matches another slide's title.

    Could be intentional (related sub-slides like "Plan de presupuesto" 23/24/25
    in the Ferreyros deck) or a copy-paste oversight. Surface but don't
    auto-penalize — the user decides.
    """
    from collections import defaultdict

    groups: dict[str, list[int]] = defaultdict(list)
    for slide in deck.get("slides", []):
        title = (slide.get("title") or "").strip()
        if title:
            groups[title].append(slide["slide_number"])

    duplicates = [
        {"title": t, "slide_numbers": nums}
        for t, nums in groups.items()
        if len(nums) >= 2
    ]
    duplicates.sort(key=lambda d: -len(d["slide_numbers"]))

    return {
        "applicable": True,
        "ok": not duplicates,
        "duplicates": duplicates,
        "notes": (
            f"{len(duplicates)} título(s) repetido(s): "
            + ", ".join(f"'{d['title'][:40]}' en {d['slide_numbers']}" for d in duplicates[:3])
            + ("..." if len(duplicates) > 3 else "")
            if duplicates
            else "Todos los títulos son únicos."
        ),
    }


# ---------------------------------------------------------------------------
# Linguistic checks (Minsait playbook page 26 — "Consistencia del lenguaje")
# ---------------------------------------------------------------------------
#
# These six checks operationalize the explicit rules from the Minsait/MBB
# "Presentaciones estructuradas" training deck:
#   1. Paralelismo en bullets (verbo vs sustantivo en primera palabra)
#   2. Verbos de acción vs verbos vinculantes en bullets
#   3. Anglicismos en cursiva
#   4. Consistencia de negritas
#   5. Detección de supertítulo / kicker
#   6. Etiquetas de tipo de slide (preliminar / backup / discusión / etc.)


# Spanish binding/copular verbs — when these dominate a bullet list, the
# slide is descriptive rather than action-oriented. From Minsait page 26:
# "Verbos - siempre verbos de acción o siempre verbos vinculantes".
_BINDING_VERBS = frozenset({
    # ser
    "es", "son", "era", "eran", "fue", "fueron", "será", "serán", "sea", "sean",
    "siendo", "sido",
    # estar
    "está", "están", "estaba", "estaban", "estuvo", "estuvieron", "estará",
    "estarán", "esté", "estén", "estando", "estado",
    # haber (auxiliar)
    "hay", "había", "habían", "hubo", "habrá", "habrán", "haya", "hayan",
    # tener
    "tiene", "tienen", "tenía", "tenían", "tuvo", "tuvieron", "tendrá",
    "tendrán", "tenga", "tengan",
})

# Common Spanish action verbs (infinitive + imperative) used in consulting
# decks. Used as a positive identifier — if the first word matches, it's an
# action verb. This is non-exhaustive; the fallback is the -ar/-er/-ir
# infinitive heuristic.
_ACTION_VERBS_HINT = frozenset({
    "definir", "diseñar", "implementar", "ejecutar", "evaluar", "medir",
    "optimizar", "automatizar", "mejorar", "reducir", "incrementar",
    "aumentar", "validar", "verificar", "auditar", "analizar", "identificar",
    "priorizar", "estructurar", "planificar", "integrar", "gestionar",
    "motivar", "formar", "capacitar", "monitorear", "monitorizar",
    "aplicar", "establecer", "construir", "crear", "lanzar", "desarrollar",
    "desplegar", "consolidar", "estandarizar", "alinear", "facilitar",
    "habilitar", "soportar", "asegurar", "garantizar", "transformar",
    "rediseñar", "redefinir", "renegociar", "captar", "retener", "fidelizar",
    "segmentar", "perfilar", "diagnosticar",
})

# Common anglicisms in consulting Spanish. Per Minsait page 26: when used,
# must appear in italics. We flag any anglicism that's not italicized.
_COMMON_ANGLICISMS = frozenset({
    # Process / strategy
    "deadline", "milestone", "kickoff", "kick-off", "workshop", "framework",
    "roadmap", "pipeline", "backlog", "scope", "deliverable", "deliverables",
    "stakeholder", "stakeholders", "input", "inputs", "output", "outputs",
    "target", "targets", "benchmark", "benchmarks", "insight", "insights",
    "feedback", "engagement", "ownership", "leadership", "performance",
    "outsourcing", "onboarding", "offboarding", "briefing", "debriefing",
    # Sales / marketing
    "lead", "leads", "prospect", "prospects", "funnel", "churn", "uplift",
    "cross-sell", "upsell", "go-to-market", "branding", "claim",
    # Operations / tech
    "core", "asset", "issue", "issues", "tracker", "dashboard", "report",
    "reporting", "scoring", "tracking", "compliance", "governance",
    # Agile / project mgmt
    "sprint", "scrum", "standup", "agile", "mvp", "okr", "okrs", "kpi",
    "kpis", "roi", "tco",
    # Meeting / communication
    "meeting", "call", "follow-up", "followup", "follow up",
})


_SPANISH_STOPWORDS_FIRST = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o",
    "de", "del", "en", "con", "sin", "por", "para", "al",
    "a", "lo", "mi", "tu", "su",
})


def _first_significant_token(text: str) -> str:
    """Return the first non-stopword token of a bullet (lowercased)."""
    if not text:
        return ""
    # Strip leading bullet markers and punctuation
    cleaned = re.sub(r"^[\s\-–—•▪●○◦*·∙]+", "", text).strip()
    # Skip leading numbering (1., 1), 1- )
    cleaned = re.sub(r"^\d+[\.\)\-]\s+", "", cleaned)
    words = cleaned.split()
    for w in words:
        # Strip surrounding punctuation
        clean = re.sub(r"^[\"'¿¡(\[\{]+|[\"',.;:!?\)\]\}]+$", "", w).lower()
        if clean and clean not in _SPANISH_STOPWORDS_FIRST:
            return clean
    return ""


def _classify_token_pos(token: str) -> str:
    """Classify a Spanish word as 'verb' / 'noun' / 'adjective' / 'unknown'.

    Heuristic — not a full POS tagger. Catches the common patterns in
    consulting bullets: infinitives (-ar/-er/-ir), gerunds (-ando/-iendo),
    participles (-ado/-ido), explicit verb whitelist, and binding verbs.
    Everything else defaults to 'noun' (which is the most common other class
    in bullet-first-word slots).
    """
    if not token:
        return "unknown"
    if token in _BINDING_VERBS:
        return "binding_verb"
    if token in _ACTION_VERBS_HINT:
        return "verb"
    # Infinitive / gerund / participle endings — strong verb signal.
    if re.search(r"(ar|er|ir)$", token) and len(token) >= 4:
        return "verb"
    if re.search(r"(ando|iendo|yendo)$", token):
        return "verb"
    if re.search(r"(ado|ido|edo)$", token) and len(token) >= 5:
        # could be noun (estado, partido) or participle; treat as verb-ish
        return "verb"
    # 3rd-person plural action verbs ending in -an/-en/-on (común en bullets:
    # "Optimizan procesos", "Definen estrategia") — only if long enough.
    if len(token) >= 6 and re.search(r"(an|en|on)$", token):
        return "verb"
    return "noun"


def _bullets_from_shape(shape: dict[str, Any]) -> list[str]:
    """Return the list of bullet strings for a shape.

    A "bullet" is one paragraph in a multi-paragraph text frame — or a line
    in a single-paragraph text frame that explicitly uses bullet markers.
    """
    paragraphs = shape.get("paragraphs") or []
    if len(paragraphs) >= 2:
        return [p["text"] for p in paragraphs if (p.get("text") or "").strip()]
    # Single-paragraph fallback: split on newlines if they look like bullets
    if len(paragraphs) == 1:
        text = (paragraphs[0].get("text") or "").strip()
        lines = [
            line for line in text.split("\n")
            if line.strip() and re.match(r"^[\s\-–—•▪●○◦*·∙]+", line)
        ]
        if len(lines) >= 2:
            return lines
    return []


def check_bullet_parallelism(slide: dict[str, Any]) -> dict[str, Any]:
    """Flag bullet lists that mix verb-first and noun-first items.

    Minsait page 26: "Primera palabra — siempre verbos o siempre sustantivos".
    Triggers only on shapes with ≥3 bullets where the first-word POS class
    isn't homogeneous (≥80% of one class). Below 80% the list is considered
    mixed and worth flagging.
    """
    findings: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        bullets = _bullets_from_shape(shape)
        if len(bullets) < 3:
            continue
        first_words = [_first_significant_token(b) for b in bullets]
        classes = [_classify_token_pos(w) for w in first_words]
        # Collapse binding_verb + verb for the homogeneity check (both are
        # verbs); the binding_verb-vs-action_verb distinction lives in its
        # own check.
        normalized = ["verb" if c in ("verb", "binding_verb") else c for c in classes]
        # Filter out 'unknown' (empty first word) for the ratio calc.
        meaningful = [c for c in normalized if c != "unknown"]
        if len(meaningful) < 3:
            continue
        from collections import Counter
        counts = Counter(meaningful)
        dominant, dominant_count = counts.most_common(1)[0]
        ratio = dominant_count / len(meaningful)
        if ratio >= 0.8:
            continue  # consistent enough
        # Mixed — flag it.
        examples = [
            {"text": b[:80], "first_word": w, "class": c}
            for b, w, c in zip(bullets, first_words, classes)
            if c != "unknown"
        ]
        findings.append({
            "shape_name": shape.get("name"),
            "bullet_count": len(bullets),
            "dominant_class": dominant,
            "dominant_ratio": round(ratio, 2),
            "counts": dict(counts),
            "examples": examples[:6],
        })

    if not findings:
        return {
            "applicable": False,
            "ok": True,
            "notes": "No hay bullet lists multi-item para evaluar paralelismo.",
            "findings": [],
            "suggestion": None,
        }

    suggestion = (
        "Reescribir los bullets para que TODOS empiecen con verbo (de acción) "
        "o TODOS con sustantivo. El estándar Minsait exige paralelismo en "
        "listas — mezclar 'Optimizar X' con 'Reducción de Y' rompe el ritmo "
        "y oculta la línea argumental."
    )
    return {
        "applicable": True,
        "ok": False,
        "findings": findings,
        "notes": (
            f"{len(findings)} bullet list(s) sin paralelismo en la primera "
            "palabra (mezcla verbo + sustantivo)."
        ),
        "suggestion": suggestion,
    }


def check_action_verbs_in_bullets(slide: dict[str, Any]) -> dict[str, Any]:
    """Flag bullet lists dominated by binding verbs (ser/estar/tener/haber).

    Per Minsait page 26: "siempre verbos de acción o siempre verbos vinculantes".
    Slides for senior decision-makers should use action verbs. A list where
    >50% of bullets start with a binding verb signals descriptive prose
    rather than recommendation-driven content.
    """
    findings: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        bullets = _bullets_from_shape(shape)
        if len(bullets) < 3:
            continue
        first_words = [_first_significant_token(b) for b in bullets]
        binding = [w for w in first_words if w in _BINDING_VERBS]
        if len(binding) == 0:
            continue
        ratio = len(binding) / len(first_words)
        if ratio >= 0.5:
            findings.append({
                "shape_name": shape.get("name"),
                "bullet_count": len(bullets),
                "binding_count": len(binding),
                "binding_ratio": round(ratio, 2),
                "binding_words": list(dict.fromkeys(binding))[:6],
                "examples": [
                    b[:80] for b, w in zip(bullets, first_words)
                    if w in _BINDING_VERBS
                ][:4],
            })

    if not findings:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Los bullets usan verbos de acción o no aplican.",
            "findings": [],
            "suggestion": None,
        }

    return {
        "applicable": True,
        "ok": False,
        "findings": findings,
        "notes": (
            f"{len(findings)} bullet list(s) dominadas por verbos vinculantes "
            "(es / son / está / tiene). El estándar Minsait prefiere verbos de "
            "acción en bullets orientados a recomendación."
        ),
        "suggestion": (
            "Reformular los bullets con verbos de acción: en vez de 'Es "
            "necesario X', usar 'Definir / implementar / evaluar X'. Si el "
            "objetivo de la slide es descriptivo (no recomendación), está OK "
            "—el alerta es para slides de propuesta/conclusión."
        ),
    }


def check_anglicisms(slide: dict[str, Any]) -> dict[str, Any]:
    """Flag anglicisms used without italic formatting.

    Per Minsait page 26: "Minimización de anglicismos - uso mínimo de
    anglicismos y, cuando se utilizan, estos deben señalarse en cursiva".

    We check every text run on the slide. An anglicism in a non-italic run
    is a finding. An anglicism in an italic run is correct usage.
    """
    findings: list[dict[str, Any]] = []
    correct_italic: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        for para in shape.get("paragraphs") or []:
            for run in para.get("runs") or []:
                text = (run.get("text") or "").strip()
                if not text:
                    continue
                # Tokenize on whitespace + punctuation; check each lowercased token.
                tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
                hit = next((t for t in tokens if t in _COMMON_ANGLICISMS), None)
                if not hit:
                    continue
                is_italic = run.get("italic") is True
                entry = {
                    "shape_name": shape.get("name"),
                    "term": hit,
                    "snippet": run.get("text", "")[:80],
                    "italic": is_italic,
                }
                if is_italic:
                    correct_italic.append(entry)
                else:
                    findings.append(entry)

    if not findings and not correct_italic:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Sin anglicismos detectados.",
            "findings": [],
            "correct_italic": [],
            "suggestion": None,
        }

    if not findings:
        return {
            "applicable": True,
            "ok": True,
            "notes": (
                f"{len(correct_italic)} anglicismo(s) detectado(s), todos en "
                "cursiva — uso correcto según el estándar Minsait."
            ),
            "findings": [],
            "correct_italic": correct_italic,
            "suggestion": None,
        }

    terms = sorted({f["term"] for f in findings})
    return {
        "applicable": True,
        "ok": False,
        "findings": findings,
        "correct_italic": correct_italic,
        "notes": (
            f"{len(findings)} anglicismo(s) sin cursiva: {', '.join(terms[:5])}"
            + ("..." if len(terms) > 5 else "")
        ),
        "suggestion": (
            "Pasar los anglicismos a cursiva (italic) o reemplazarlos por su "
            "equivalente en español: 'deadline' → 'fecha límite', 'meeting' "
            "→ 'reunión', 'feedback' → 'retroalimentación'. Si el término "
            "técnico no tiene equivalente, mantenerlo en cursiva."
        ),
    }


def check_bold_consistency(slide: dict[str, Any]) -> dict[str, Any]:
    """Flag inconsistent bold emphasis within the slide body.

    Per Minsait page 26: "Negritas — siempre énfasis en el mismo tipo de
    objetos (p.ej. verbos, sustantivos, adjetivos)".

    Heuristic: collect every bold-emphasized run on the slide. Classify each
    as numeric (mostly digits/%) or textual. If a slide mixes numeric and
    textual bolding without a clear majority, flag it. Slides with very few
    bold runs are exempt.
    """
    bold_items: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        for para in shape.get("paragraphs") or []:
            for run in para.get("runs") or []:
                if run.get("bold") is not True:
                    continue
                text = (run.get("text") or "").strip()
                if not text:
                    continue
                bold_items.append({
                    "shape_name": shape.get("name"),
                    "text": text[:60],
                })

    if len(bold_items) < 3:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Pocas negritas en el body para evaluar consistencia.",
            "bold_count": len(bold_items),
            "items": bold_items,
            "suggestion": None,
        }

    # Classify each bold item: 'numeric' if text is mostly digits/%/currency
    # symbols/scale suffixes (M/K/B/bn/USD), else 'text'.
    _SCALE_SUFFIX_RE = re.compile(
        r"^\s*[+\-]?\$?\d[\d.,]*\s*(%|pp|bps|x|usd|eur|m|mm|mn|k|b|bn|tn)?\s*$",
        re.IGNORECASE,
    )

    def _classify(t: str) -> str:
        stripped = t.strip()
        if not stripped:
            return "text"
        # Whole-string match against the numeric pattern (handles "$5M",
        # "30%", "+12pp", "1.2bn", "USD 5M").
        if _SCALE_SUFFIX_RE.match(stripped):
            return "numeric"
        chars = [c for c in t if not c.isspace()]
        if not chars:
            return "text"
        digit_like = sum(
            1 for c in chars
            if c.isdigit() or c in "%$€£¥.,+-"
        )
        if digit_like / len(chars) >= 0.7:
            return "numeric"
        return "text"

    classes = [_classify(it["text"]) for it in bold_items]
    from collections import Counter
    counts = Counter(classes)
    dominant, dominant_count = counts.most_common(1)[0]
    ratio = dominant_count / len(classes)

    if ratio >= 0.8 or len(counts) == 1:
        return {
            "applicable": True,
            "ok": True,
            "bold_count": len(bold_items),
            "dominant_class": dominant,
            "counts": dict(counts),
            "items": bold_items[:10],
            "notes": (
                f"Negritas consistentes: {dominant_count}/{len(classes)} son "
                f"{dominant} (énfasis homogéneo)."
            ),
            "suggestion": None,
        }

    return {
        "applicable": True,
        "ok": False,
        "bold_count": len(bold_items),
        "dominant_class": dominant,
        "counts": dict(counts),
        "items": bold_items[:10],
        "notes": (
            f"Énfasis en negrita mixto: {dict(counts)} (cifras + texto sin "
            "criterio dominante)."
        ),
        "suggestion": (
            "Decidir UN solo criterio para negritas y aplicarlo a toda la "
            "slide: o se destacan solo cifras clave (KPIs, porcentajes), o "
            "solo conceptos / verbos de acción. Mezclar pierde el énfasis "
            "porque la audiencia no sabe qué mirar primero."
        ),
    }


def check_kicker(slide: dict[str, Any]) -> dict[str, Any]:
    """Detect a kicker / supertítulo above the slide title.

    Per Minsait page 21 ("Descomponiendo una diapositiva"), the supertítulo
    is one of the 8 slide elements: a short label (numeric/descriptive/visual)
    placed above the main title for context.

    Geometric heuristic:
    - Title shape exists
    - There's a non-title text shape directly above the title (top + height < title.top)
    - That shape is short (< 60 chars) and uses a smaller font than the title
    """
    title_shape = next(
        (sh for sh in slide.get("shapes", []) if sh.get("is_title")), None
    )
    if not title_shape:
        return {
            "applicable": False,
            "present": False,
            "notes": "Sin título — no se evalúa supertítulo.",
        }
    title_top = title_shape.get("top_in")
    title_height = title_shape.get("height_in")
    title_size = title_shape.get("min_font_size_pt")
    if title_top is None:
        return {
            "applicable": False,
            "present": False,
            "notes": "Sin geometría del título.",
        }

    for shape in slide.get("shapes", []):
        if shape.get("is_title"):
            continue
        top = shape.get("top_in")
        height = shape.get("height_in")
        text = (shape.get("text") or "").strip()
        if top is None or not text:
            continue
        # Above the title (bottom edge of this shape ≤ top of title)
        bottom = top + (height or 0)
        if bottom > title_top + 0.1:
            continue
        if len(text) > 60:
            continue
        sh_size = shape.get("min_font_size_pt")
        smaller = (
            title_size is None
            or sh_size is None
            or sh_size < title_size
        )
        if not smaller:
            continue
        return {
            "applicable": True,
            "present": True,
            "kicker_text": text,
            "kicker_top_in": top,
            "title_top_in": title_top,
            "notes": f"Supertítulo detectado: \"{text[:50]}\".",
            "suggestion": None,
        }
    return {
        "applicable": True,
        "present": False,
        "notes": "Sin supertítulo (puede ser intencional o un slot vacío).",
        "suggestion": None,
    }


# Slide-type labels per Minsait page 21 — these tags signal the slide's
# editorial status. Detection is best-effort: keyword match in any text shape.
_SLIDE_TYPE_LABELS = {
    "preliminar": ("preliminar", "borrador", "draft", "preliminary"),
    "backup": ("backup", "respaldo", "appendix", "anexo"),
    "ilustrativa": ("ilustrativa", "ilustrativo", "illustrative"),
    "no_exhaustiva": (
        "no exhaustiva", "no exhaustivo", "non-exhaustive",
        "not exhaustive",
    ),
    "discusion": (
        "para discusión", "para discusion", "discusión", "for discussion",
        "discussion",
    ),
}


def check_slide_type_label(slide: dict[str, Any]) -> dict[str, Any]:
    """Detect editorial slide-type tags (preliminar / backup / discusión / etc.).

    Looks at every text shape on the slide for the keywords from
    `_SLIDE_TYPE_LABELS`. Detection is informational — these labels are
    legitimate per the Minsait playbook; we surface them so the user can
    confirm they're being applied consistently across the deck.
    """
    detected: list[dict[str, Any]] = []
    for shape in slide.get("shapes", []):
        text = (shape.get("text") or "").strip().lower()
        if not text or len(text) > 120:
            continue
        for label, keywords in _SLIDE_TYPE_LABELS.items():
            for kw in keywords:
                if kw in text:
                    detected.append({
                        "label": label,
                        "matched_text": (shape.get("text") or "").strip()[:60],
                        "shape_name": shape.get("name"),
                    })
                    break

    if not detected:
        return {
            "applicable": False,
            "present": False,
            "labels": [],
            "notes": "Sin etiquetas de tipo de slide.",
        }

    labels = sorted({d["label"] for d in detected})
    return {
        "applicable": True,
        "present": True,
        "labels": labels,
        "detected": detected,
        "notes": (
            f"Etiqueta(s) de tipo: {', '.join(labels)}."
        ),
        "suggestion": None,
    }


# ---------------------------------------------------------------------------
# Deck-level rollups for the new linguistic checks
# ---------------------------------------------------------------------------

def check_anglicism_consistency(deck: dict[str, Any]) -> dict[str, Any]:
    """Roll up anglicism usage across the deck for the overview panel."""
    total_uses = 0
    italic_uses = 0
    non_italic_uses = 0
    term_counter: dict[str, int] = {}
    offending_slides: list[int] = []
    for slide in deck.get("slides", []):
        result = check_anglicisms(slide)
        if not result.get("applicable"):
            continue
        for f in result.get("findings", []):
            total_uses += 1
            non_italic_uses += 1
            term_counter[f["term"]] = term_counter.get(f["term"], 0) + 1
            if slide["slide_number"] not in offending_slides:
                offending_slides.append(slide["slide_number"])
        for f in result.get("correct_italic", []):
            total_uses += 1
            italic_uses += 1
            term_counter[f["term"]] = term_counter.get(f["term"], 0) + 1

    if total_uses == 0:
        return {
            "applicable": False,
            "ok": True,
            "notes": "El deck no usa anglicismos comunes.",
            "total_uses": 0,
        }

    top_terms = sorted(term_counter.items(), key=lambda kv: -kv[1])[:6]
    italic_pct = italic_uses / total_uses if total_uses else 0.0
    return {
        "applicable": True,
        "ok": non_italic_uses == 0,
        "total_uses": total_uses,
        "italic_uses": italic_uses,
        "non_italic_uses": non_italic_uses,
        "italic_pct": round(italic_pct, 2),
        "top_terms": top_terms,
        "offending_slides": sorted(offending_slides),
        "notes": (
            f"{total_uses} anglicismo(s) en el deck — "
            f"{italic_uses} en cursiva (correcto), "
            f"{non_italic_uses} sin cursiva."
            if non_italic_uses
            else f"{total_uses} anglicismo(s), todos en cursiva: uso correcto."
        ),
        "suggestion": (
            "Anglicismos sin cursiva en " + str(len(offending_slides))
            + " slide(s). Pasarlos a italic o reemplazar por equivalente "
            "en español."
            if non_italic_uses else None
        ),
    }


def check_kicker_consistency(deck: dict[str, Any]) -> dict[str, Any]:
    """Across content slides, % with vs without kicker.

    If the deck uses kickers, they should appear on a consistent set of
    slides (e.g. all content slides). A 30/70 mix signals editorial drift.
    """
    body_slides_with_kicker = 0
    body_slides_total = 0
    kicker_slides: list[int] = []
    no_kicker_slides: list[int] = []
    for slide in deck.get("slides", []):
        role = classify_slide_role(slide)
        if role not in ("content_with_title",):
            continue
        body_slides_total += 1
        k = check_kicker(slide)
        if k.get("present"):
            body_slides_with_kicker += 1
            kicker_slides.append(slide["slide_number"])
        else:
            no_kicker_slides.append(slide["slide_number"])

    if body_slides_total < 3:
        return {
            "applicable": False,
            "ok": True,
            "notes": "Pocos content slides para evaluar consistencia de kicker.",
        }

    coverage = body_slides_with_kicker / body_slides_total
    # Consistent if either ≥80% use it or ≤10% use it (deck-wide convention).
    consistent = coverage >= 0.8 or coverage <= 0.1
    return {
        "applicable": True,
        "ok": consistent,
        "body_slides_total": body_slides_total,
        "body_slides_with_kicker": body_slides_with_kicker,
        "coverage_pct": round(coverage, 2),
        "kicker_slides": kicker_slides,
        "no_kicker_slides": no_kicker_slides[:10],
        "notes": (
            f"{body_slides_with_kicker}/{body_slides_total} content slides "
            f"({coverage:.0%}) usan supertítulo — "
            + ("convención consistente." if consistent
               else "convención mixta, debería ser todo o nada.")
        ),
        "suggestion": (
            None if consistent else
            "Definir si el deck usa supertítulos o no. Si sí, agregarlos a "
            "todas las content slides. Si no, removerlos. La mezcla rompe "
            "el ritmo visual."
        ),
    }


def check_slide_type_label_summary(deck: dict[str, Any]) -> dict[str, Any]:
    """Aggregate slide-type labels across the deck."""
    by_label: dict[str, list[int]] = {}
    for slide in deck.get("slides", []):
        r = check_slide_type_label(slide)
        if not r.get("present"):
            continue
        for label in r.get("labels", []):
            by_label.setdefault(label, []).append(slide["slide_number"])

    if not by_label:
        return {
            "applicable": False,
            "present": False,
            "notes": "Sin etiquetas editoriales (preliminar / backup / etc.).",
            "by_label": {},
        }

    parts = [f"{lbl}: slides {nums}" for lbl, nums in by_label.items()]
    return {
        "applicable": True,
        "present": True,
        "by_label": by_label,
        "notes": "Etiquetas detectadas — " + " · ".join(parts),
        "suggestion": (
            "Confirmar que las etiquetas son intencionales. Si el deck es "
            "final, remover etiquetas tipo 'Preliminar' o 'Borrador'."
        ),
    }


def run_deterministic_checks(file_name: str, deck: dict[str, Any]) -> dict[str, Any]:
    """Apply every deterministic check; return a structured report."""
    slide_height_in = deck.get("slide_height_in")
    slide_reports = []
    total_slides = len(deck["slides"])
    for slide in deck["slides"]:
        slide_reports.append(
            {
                "slide_number": slide["slide_number"],
                "title": slide.get("title"),
                "role": classify_slide_role(slide, total_slides=total_slides),
                "paragraphs": check_slide_paragraphs(slide),
                "footer": check_footer(slide, slide_height_in),
                "min_font_size": check_min_font_size(slide),
                "text_density": check_text_density(slide),
                "font_family": check_font_family(slide),
                "title_case": check_title_not_uppercase(slide),
                "bullet_parallelism": check_bullet_parallelism(slide),
                "binding_verbs": check_action_verbs_in_bullets(slide),
                "anglicisms": check_anglicisms(slide),
                "bold_consistency": check_bold_consistency(slide),
                "kicker": check_kicker(slide),
                "slide_type_label": check_slide_type_label(slide),
            }
        )

    return {
        "file_name": file_name,
        "deck_meta": {
            "slide_count": deck["slide_count"],
            "slide_width_in": deck.get("slide_width_in"),
            "slide_height_in": deck.get("slide_height_in"),
        },
        "slides": slide_reports,
        "footer_alignment": check_footer_alignment(deck),
        "footer_caps": check_footer_caps_consistency(deck),
        "footer_text_consistency": check_footer_text_consistency(deck),
        "footer_matches_deck_title": check_footer_matches_deck_title(deck),
        "filename_alignment": check_filename_alignment(deck, file_name),
        "subtitle_filename_alignment": check_subtitle_filename_alignment(deck, file_name),
        "title_format_consistency": check_title_format_consistency(deck),
        "duplicate_titles": check_duplicate_titles(deck),
        "anglicism_consistency": check_anglicism_consistency(deck),
        "kicker_consistency": check_kicker_consistency(deck),
        "slide_type_labels": check_slide_type_label_summary(deck),
    }
