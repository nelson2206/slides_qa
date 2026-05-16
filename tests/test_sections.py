from __future__ import annotations

from sections import detect_sections, is_auto_skip_section


def _slide(n: int, title: str = "", layout: str = "Title and Content", body_text: str = "") -> dict:
    shapes = [{"is_title": True, "text": title}] if title else []
    if body_text:
        shapes.append({"is_title": False, "text": body_text})
    return {
        "slide_number": n,
        "layout_name": layout,
        "title": title or None,
        "shapes": shapes,
    }


def test_detect_sections_returns_none_when_few_dividers():
    deck = {"slides": [_slide(1, "Cover"), _slide(2, "Content", body_text="x" * 200)]}
    assert detect_sections(deck) is None


def test_detect_sections_groups_by_dividers():
    deck = {
        "slides": [
            _slide(1, "Cover", layout="Title Slide"),
            _slide(2, "Body 1", body_text="x" * 200),
            _slide(3, "Sección A", layout="Section Header"),
            _slide(4, "Body A1", body_text="x" * 200),
            _slide(5, "Body A2", body_text="x" * 200),
            _slide(6, "Sección B", layout="Section Header"),
            _slide(7, "Body B1", body_text="x" * 200),
        ]
    }
    sections = detect_sections(deck)
    assert sections is not None
    names = [s["name"] for s in sections]
    assert "Apertura" in names
    assert "Sección A" in names
    assert "Sección B" in names
    section_a = next(s for s in sections if s["name"] == "Sección A")
    assert section_a["start"] == 3
    assert section_a["end"] == 5


def test_is_auto_skip_section_matches_boilerplate():
    for name in (
        "Carátula", "Portada",
        "Avisos de confidencialidad", "Aviso legal", "Disclaimer",
        "Índice", "Agenda", "Tabla de contenidos",
        "Referencias", "Casos de éxito", "Nuestros clientes",
        "Credenciales",
        "CVs de consultores", "Currículum del equipo",
        "Cierre", "Gracias", "Preguntas",
    ):
        assert is_auto_skip_section(name) is True, f"Should auto-skip: {name!r}"


def test_is_auto_skip_section_keeps_content_sections():
    for name in (
        "Contexto y Objetivos",
        "Nuestro enfoque",
        "Valor añadido y aceleradores Minsait",
        "Metodología de trabajo",
        "Plan de trabajo",
        "Equipo de trabajo",
    ):
        assert is_auto_skip_section(name) is False, f"Should NOT auto-skip: {name!r}"


def test_detect_sections_marks_boilerplate_with_auto_skip():
    deck = {
        "slides": [
            _slide(1, "Cover", layout="Title Slide"),
            _slide(2, "Referencias", layout="Section Header"),
            _slide(3, "Cliente 1"),
            _slide(4, "Cliente 2"),
            _slide(5, "Contexto y Objetivos", layout="Section Header"),
            _slide(6, "Body", body_text="x" * 200),
        ]
    }
    sections = detect_sections(deck)
    assert sections is not None
    refs = next(s for s in sections if s["name"] == "Referencias")
    ctx = next(s for s in sections if s["name"] == "Contexto y Objetivos")
    assert refs["auto_skip"] is True
    assert ctx["auto_skip"] is False
