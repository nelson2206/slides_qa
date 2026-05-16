"""Section detection — group slides by divider boundaries.

When a deck has a clear structure (≥2 divider slides), we expose section-level
controls so the user can opt-out of whole chapters before running the analysis.
If the index isn't clear (< 2 dividers), `detect_sections` returns None and the
app falls back to the regular role-based skip behaviour.

Section names matching common boilerplate patterns (confidencialidad, índice,
referencias, credenciales, CVs, cierre) are flagged with `auto_skip=True` so
the pre-run UI starts them unchecked by default.
"""
from __future__ import annotations

from typing import Any

from checks import _normalize_title_for_match, classify_slide_role

# Section names whose default state in the picker should be UNCHECKED.
# These typically don't carry analyzable narrative — they're cover/legal/refs/CVs.
_AUTO_SKIP_SECTION_KEYWORDS = (
    "caratula", "portada", "cover",
    "confidencialidad", "aviso legal", "disclaimer",
    "agenda", "indice", "contenido", "contenidos",
    "tabla de contenido", "tabla de contenidos", "table of contents", "outline",
    "referencias", "casos de exito", "case studies", "nuestros clientes",
    "credenciales", "credentials",
    "cv", "cvs", "curriculum",
    "perfil del equipo", "perfiles del equipo", "consultores asignados",
    "gracias", "preguntas", "contacto", "the end", "cierre",
)


def is_auto_skip_section(name: str) -> bool:
    """True if the section name matches a known boilerplate pattern."""
    if not name:
        return False
    name_norm = _normalize_title_for_match(name)
    if not name_norm:
        return False
    words = name_norm.split()
    for kw in _AUTO_SKIP_SECTION_KEYWORDS:
        if len(kw) <= 3:
            if kw in words:
                return True
        elif kw in name_norm:
            return True
    return False


def detect_sections(deck: dict[str, Any]) -> list[dict] | None:
    """Detect deck sections from divider slides.

    Returns a list of `{name, start, end, slide_numbers}` dicts (slide_numbers
    are 1-indexed and inclusive), or `None` if the deck lacks ≥2 dividers.
    """
    slides = deck.get("slides", [])
    if not slides:
        return None

    dividers: list[dict[str, Any]] = []
    for s in slides:
        # Prefer the pre-classified role if present (works on both raw deck slides
        # and on per-slide findings from a qa result, which carry .role).
        role = s.get("role") or classify_slide_role(s)
        if role == "divider":
            n = s.get("slide_number", 0)
            if n <= 0:
                continue
            # Title can live under .title (raw deck) or .action_title.current_title (finding).
            title = (s.get("title") or "").strip()
            if not title:
                at = s.get("action_title") or {}
                title = (at.get("current_title") or "").strip()
            dividers.append({"slide_number": n, "title": title})

    if len(dividers) < 2:
        return None

    sections: list[dict[str, Any]] = []
    total = len(slides)

    first_div = dividers[0]["slide_number"]
    if first_div > 1:
        sections.append({
            "name": "Apertura",
            "start": 1,
            "end": first_div - 1,
            "slide_numbers": list(range(1, first_div)),
            "auto_skip": True,  # apertura usually = carátula + confidencialidad + índice
        })

    for i, div in enumerate(dividers):
        start = div["slide_number"]
        end = dividers[i + 1]["slide_number"] - 1 if i + 1 < len(dividers) else total
        if start > end:
            continue
        name = div["title"] or f"Sección {i + 1}"
        sections.append({
            "name": name,
            "start": start,
            "end": end,
            "slide_numbers": list(range(start, end + 1)),
            "auto_skip": is_auto_skip_section(name),
        })

    return sections if sections else None


def section_for_slide(sections: list[dict] | None, slide_number: int) -> dict | None:
    """Return the section dict containing this slide, or None."""
    if not sections:
        return None
    for sec in sections:
        if sec["start"] <= slide_number <= sec["end"]:
            return sec
    return None
