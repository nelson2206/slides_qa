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
    }
