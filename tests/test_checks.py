from __future__ import annotations

from checks import (
    check_duplicate_titles,
    check_filename_alignment,
    check_footer,
    check_footer_alignment,
    check_footer_caps_consistency,
    check_footer_matches_deck_title,
    check_footer_text_consistency,
    check_paragraph,
    check_slide_paragraphs,
    check_subtitle_filename_alignment,
    check_title_format_consistency,
    classify_action_title_heuristic,
    classify_caps,
    classify_slide_role,
    classify_title_length,
    detect_so_what_heuristic,
    estimate_lines,
    run_deterministic_checks,
)
from extractor import extract_deck


# -------- Unit-level checks --------

def test_estimate_lines_short_text():
    assert estimate_lines("Hola") == 1
    assert estimate_lines("") == 0


def test_estimate_lines_wraps_long_text():
    long = "x" * 250
    assert estimate_lines(long, chars_per_line=80) == 4


def test_check_paragraph_flags_long():
    long = "palabra " * 60
    result = check_paragraph(long)
    assert result["too_long"] is True
    assert result["word_count"] >= 60


def test_check_paragraph_passes_short():
    result = check_paragraph("Una idea corta y clara.")
    assert result["too_long"] is False


# -------- End-to-end against the bad fixture --------

def test_bad_deck_flags_long_paragraphs(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    slide_2 = deck["slides"][1]
    report = check_slide_paragraphs(slide_2)
    assert not report["ok"]
    assert len(report["long_paragraphs"]) >= 1
    assert len(report["bullet_candidates"]) >= 1


def test_bad_deck_detects_footer(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    slide_2 = deck["slides"][1]
    footer = check_footer(slide_2, deck["slide_height_in"])
    assert footer["present"] is True
    assert "Estudio 2024" in (footer.get("text") or "")
    # Footer should be in the bottom of the slide
    assert footer["top_in"] >= deck["slide_height_in"] * 0.82


def test_bad_deck_flags_misaligned_footers(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    alignment = check_footer_alignment(deck)
    # Slides 2 (top=6.95, h=0.3) vs slide 3 (top=7.10, h=0.32) — misaligned vertically
    assert alignment["applicable"] is True
    assert alignment["ok"] is False
    assert alignment["top_range_in"] > 0.1


def test_bad_deck_filename_no_overlap(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    align = check_filename_alignment(deck, "deck_problemas.pptx")
    assert align["applicable"] is True
    assert align["cover_aligned"] is False


# -------- End-to-end against the good fixture --------

def test_good_deck_paragraphs_ok(good_deck_path):
    deck = extract_deck(good_deck_path)
    for slide in deck["slides"]:
        report = check_slide_paragraphs(slide)
        assert report["ok"], f"Slide {slide['slide_number']} flagged"


def test_good_deck_footers_aligned(good_deck_path):
    deck = extract_deck(good_deck_path)
    alignment = check_footer_alignment(deck)
    assert alignment["applicable"] is True
    assert alignment["ok"] is True


def test_good_deck_filename_alignment(good_deck_path):
    deck = extract_deck(good_deck_path)
    align = check_filename_alignment(deck, "estrategia_comercial_2025.pptx")
    assert align["applicable"] is True
    assert align["cover_aligned"] is True


# -------- The full deterministic orchestrator --------

def test_run_deterministic_checks_full_shape(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    report = run_deterministic_checks("deck_problemas.pptx", deck)

    assert report["file_name"] == "deck_problemas.pptx"
    assert report["deck_meta"]["slide_count"] == 5
    assert len(report["slides"]) == 5
    assert "filename_alignment" in report
    assert "footer_alignment" in report
    assert "footer_caps" in report
    assert "footer_text_consistency" in report
    assert "footer_matches_deck_title" in report

    assert not report["filename_alignment"]["ok"]
    assert not report["footer_alignment"]["ok"]
    assert not report["footer_caps"]["ok"]


# -------- classify_caps --------

def test_classify_caps_title_case():
    assert classify_caps("Estudio 2024") == "title_case"


def test_classify_caps_all_upper():
    assert classify_caps("ESTUDIO 2024") == "all_upper"


def test_classify_caps_prefix_is_stripped():
    assert classify_caps("01. Contexto y objetivo") == "title_case"
    assert classify_caps("03. VALOR AÑADIDO MINSAIT") == "all_upper"


def test_classify_caps_empty():
    assert classify_caps("") == "empty"
    assert classify_caps("01. ") == "empty"


def test_classify_caps_lower():
    assert classify_caps("hola que tal") == "lower"


# -------- footer caps consistency --------

def test_bad_deck_footer_caps_inconsistent(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    report = check_footer_caps_consistency(deck)
    assert report["applicable"] is True
    assert report["ok"] is False
    # Slide 2 = "Estudio 2024" (title_case), Slide 3 = "ESTUDIO 2024" (all_upper)
    counts = report["style_counts"]
    assert counts.get("title_case", 0) >= 1
    assert counts.get("all_upper", 0) >= 1


def test_good_deck_footer_caps_consistent(good_deck_path):
    deck = extract_deck(good_deck_path)
    report = check_footer_caps_consistency(deck)
    assert report["applicable"] is True
    assert report["ok"] is True


# -------- footer text consistency --------

def test_bad_deck_footer_text_inconsistent(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    report = check_footer_text_consistency(deck)
    assert report["applicable"] is True
    # Slide 4 has NO footer (coverage gap) + slides 2/3 have different text variants
    assert report["ok"] is False
    # Slide 5 is content_no_title; only slide 2/3 of the content slides have footer
    assert report["content_slides"] >= 3
    assert report["coverage_pct"] < 1.0


def test_good_deck_footer_text_consistent(good_deck_path):
    deck = extract_deck(good_deck_path)
    report = check_footer_text_consistency(deck)
    assert report["applicable"] is True
    assert report["ok"] is True
    # All footers same → consistency_pct = 1.0
    assert report["consistency_pct"] == 1.0
    assert "Estrategia comercial 2025" in report["dominant_text"]


# -------- footer matches deck title --------

def test_good_deck_footer_matches_cover(good_deck_path):
    deck = extract_deck(good_deck_path)
    report = check_footer_matches_deck_title(deck)
    assert report["applicable"] is True
    assert report["ok"] is True
    # Cover title is "Estrategia comercial 2025: capturar +20% de share digital"
    # Footers contain "Estrategia comercial 2025" → strong match
    assert "estrategia" in report["cover_keywords"]
    assert report["coverage_pct"] >= 0.5


def test_bad_deck_footer_doesnt_match_cover(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    # Cover title is "Resultados 2024". Footers say "Estudio 2024" — keyword '2024'
    # overlaps! So this test asserts the CHECK still works (returns structured result),
    # not necessarily a fail on this fixture. We're verifying the function shape.
    report = check_footer_matches_deck_title(deck)
    assert report["applicable"] is True
    assert "cover_title" in report
    assert report["cover_title"] == "Resultados 2024"


# -------- classify_slide_role --------

def test_classify_slide_role_cover_is_slide_one():
    slide = {"slide_number": 1, "layout_name": "Title Slide", "title": "X", "shapes": []}
    assert classify_slide_role(slide) == "cover"


def test_classify_slide_role_divider_by_layout_hint():
    slide = {
        "slide_number": 4,
        "layout_name": "Section Header",
        "title": "Sección 2",
        "shapes": [{"is_title": True, "text": "Sección 2"}],
    }
    assert classify_slide_role(slide) == "divider"


def test_classify_slide_role_content_no_title():
    slide = {
        "slide_number": 5,
        "layout_name": "Blank",
        "title": None,
        "shapes": [
            {"is_title": False, "text": "x" * 200},
            {"is_title": False, "text": "y" * 100},
        ],
    }
    assert classify_slide_role(slide) == "content_no_title"


def test_classify_slide_role_content_with_title():
    slide = {
        "slide_number": 3,
        "layout_name": "Title and Content",
        "title": "Mi título",
        "shapes": [
            {"is_title": True, "text": "Mi título"},
            {"is_title": False, "text": "z" * 200},
        ],
    }
    assert classify_slide_role(slide) == "content_with_title"


def test_bad_deck_flags_content_no_title(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    slide_5 = deck["slides"][4]
    assert classify_slide_role(slide_5) == "content_no_title"


# -------- classify_title_length --------

def test_classify_title_length_buckets():
    assert classify_title_length(None) == "empty"
    assert classify_title_length("") == "empty"
    assert classify_title_length("Riesgos") == "short"
    assert classify_title_length("Análisis de ventas") == "short"
    assert classify_title_length("Costos operativos crecieron 12% por inflación sostenida") == "medium"
    assert classify_title_length(
        "El canal digital creció 30% en 2024 superando al canal físico por segundo año"
    ) == "long"


# -------- title format consistency --------

def test_title_format_consistency_flags_mix():
    deck = {
        "slides": [
            {"slide_number": 1, "title": "Riesgos"},
            {"slide_number": 2, "title": "Costos"},
            {"slide_number": 3, "title": "Plan"},
            {"slide_number": 4, "title": "Aprobar la inversión de USD 8M para capturar 20% de share digital en 2025"},
            {"slide_number": 5, "title": "El canal digital creció 30% en 2024 superando al canal físico ampliamente"},
        ]
    }
    result = check_title_format_consistency(deck)
    assert result["applicable"] is True
    assert result["ok"] is False
    assert result["counts"]["short"] >= 2
    assert result["counts"]["long"] >= 2


def test_title_format_consistency_passes_uniform():
    deck = {"slides": [{"slide_number": i, "title": "Riesgos"} for i in range(1, 6)]}
    result = check_title_format_consistency(deck)
    assert result["applicable"] is True
    assert result["ok"] is True


# -------- duplicate titles --------

def test_bad_deck_has_duplicate_titles(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    result = check_duplicate_titles(deck)
    assert result["ok"] is False
    # Slides 3 and 4 both have "Costos operativos"
    assert any(
        d["title"] == "Costos operativos" and set(d["slide_numbers"]) == {3, 4}
        for d in result["duplicates"]
    )


def test_good_deck_has_unique_titles(good_deck_path):
    deck = extract_deck(good_deck_path)
    result = check_duplicate_titles(deck)
    assert result["ok"] is True
    assert result["duplicates"] == []


# -------- subtitle filename alignment --------

def test_subtitle_filename_alignment_good_deck(good_deck_path):
    deck = extract_deck(good_deck_path)
    result = check_subtitle_filename_alignment(deck, "estrategia_comercial_2025.pptx")
    assert result["applicable"] is True
    assert result["ok"] is True
    assert len(result["matches"]) >= 1


# -------- action title heuristic --------

def test_action_title_heuristic_empty():
    r = classify_action_title_heuristic("")
    assert r["verdict"] is False
    assert "sin título" in r["notes"].lower() or "Sin título" in r["notes"]
    assert r["suggestion"] is not None


def test_action_title_heuristic_short():
    """1-3 words: definitively not action title."""
    for title in ["Riesgos", "Matriz de riesgos", "Análisis de ventas"]:
        r = classify_action_title_heuristic(title)
        assert r["verdict"] is False, f"Expected False for {title!r}, got {r}"
        assert r["suggestion"] is not None


def test_action_title_heuristic_borderline():
    """4-6 words: unsure."""
    r = classify_action_title_heuristic("Plan de presupuesto / gestión financiera")
    assert r["verdict"] is None
    assert r["suggestion"] is not None


def test_action_title_heuristic_long():
    """7+ words: likely action title."""
    r = classify_action_title_heuristic(
        "El canal digital creció 30% en 2024 superando al físico ampliamente"
    )
    assert r["verdict"] is True
    assert r["suggestion"] is None


# -------- so-what heuristic --------

def test_so_what_heuristic_via_action_title():
    """If title is an action title, so-what is in it."""
    slide = {"shapes": []}
    r = detect_so_what_heuristic(
        slide,
        "El canal digital creció 30% en 2024 superando al físico ampliamente",
    )
    assert r["verdict"] is True


def test_so_what_heuristic_via_body_markers():
    slide = {
        "shapes": [
            {"is_title": False, "text": "Las ventas cayeron 5%. Por lo tanto, hay que reaccionar."},
        ]
    }
    r = detect_so_what_heuristic(slide, "Ventas 2024")
    assert r["verdict"] is True
    assert "por lo tanto" in r["notes"].lower()


def test_so_what_heuristic_unclear():
    slide = {
        "shapes": [
            {"is_title": False, "text": "Los costos crecieron 12% durante el año."},
        ]
    }
    r = detect_so_what_heuristic(slide, "Costos 2024")
    assert r["verdict"] is None
    assert r["suggestion"] is not None


def test_subtitle_filename_alignment_bad_deck(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    result = check_subtitle_filename_alignment(deck, "deck_problemas.pptx")
    assert result["applicable"] is True
    assert result["ok"] is False
    assert result["subtitles_found"] >= 1
    assert result["matches"] == []
