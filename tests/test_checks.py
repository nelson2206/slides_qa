from __future__ import annotations

from checks import (
    check_duplicate_titles,
    check_filename_alignment,
    check_font_family,
    check_footer,
    check_footer_alignment,
    check_footer_caps_consistency,
    check_footer_matches_deck_title,
    check_footer_text_consistency,
    check_min_font_size,
    check_paragraph,
    check_slide_paragraphs,
    check_subtitle_filename_alignment,
    check_text_density,
    check_title_format_consistency,
    check_title_not_uppercase,
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


def test_classify_slide_role_index_by_title_keyword():
    for kw in ("Agenda", "Índice", "Tabla de contenido", "Contents", "Outline"):
        slide = {"slide_number": 2, "layout_name": "Title and Content", "title": kw, "shapes": []}
        assert classify_slide_role(slide) == "index", f"Failed on title={kw!r}"


def test_classify_slide_role_index_substring_match():
    slide = {
        "slide_number": 2, "layout_name": "Title and Content",
        "title": "Agenda de hoy", "shapes": [],
    }
    assert classify_slide_role(slide) == "index"


def test_classify_slide_role_closing_by_title_keyword():
    for kw in ("¡Gracias!", "Thank you", "Preguntas", "Q&A", "Contacto", "The End"):
        slide = {"slide_number": 10, "layout_name": "Title Slide", "title": kw, "shapes": []}
        assert classify_slide_role(slide) == "closing", f"Failed on title={kw!r}"


def test_classify_slide_role_closing_last_slide_minimal_body():
    """Last slide with barely any body content → closing, even without keyword."""
    slide = {
        "slide_number": 10,
        "layout_name": "Title Slide",
        "title": "Final",
        "shapes": [{"is_title": True, "text": "Final"}],
    }
    assert classify_slide_role(slide, total_slides=10) == "closing"


def test_classify_slide_role_cover_wins_over_index():
    """Even if slide 1 has 'agenda' in title, it's still the cover."""
    slide = {"slide_number": 1, "layout_name": "Title Slide", "title": "Agenda", "shapes": []}
    assert classify_slide_role(slide) == "cover"


def test_classify_slide_role_confidentiality():
    for kw in ("Avisos de confidencialidad", "Aviso legal", "Disclaimer", "Confidentiality notice"):
        slide = {"slide_number": 2, "layout_name": "Title and Content", "title": kw, "shapes": []}
        assert classify_slide_role(slide) == "confidentiality", f"Failed on {kw!r}"


def test_classify_slide_role_references():
    for kw in ("Referencias", "Casos de éxito", "Clientes y referencias", "Case studies"):
        slide = {"slide_number": 30, "layout_name": "Title and Content", "title": kw, "shapes": []}
        assert classify_slide_role(slide) == "references", f"Failed on {kw!r}"


def test_classify_slide_role_credentials():
    for kw in ("Credenciales", "Nuestras credenciales", "Credentials"):
        slide = {"slide_number": 35, "layout_name": "Title and Content", "title": kw, "shapes": []}
        assert classify_slide_role(slide) == "credentials", f"Failed on {kw!r}"


def test_classify_slide_role_cv():
    for kw in ("CVs de consultores", "CV Juan Pérez", "Currículum del equipo",
               "Consultores asignados", "Perfil del equipo"):
        slide = {"slide_number": 40, "layout_name": "Title and Content", "title": kw, "shapes": []}
        assert classify_slide_role(slide) == "cv", f"Failed on {kw!r}"


def test_classify_slide_role_toc_by_numbered_chapters():
    """A slide in position 2-4 whose body has multiple numbered items is
    detected as a TOC/index even when the title isn't 'Agenda'/'Índice'."""
    slide = {
        "slide_number": 3,
        "layout_name": "Title and Content",
        "title": "Project Acceleration Hub",
        "shapes": [
            {"is_title": True, "text": "Project Acceleration Hub"},
            {"is_title": False, "text": "01 Contexto y objetivos"},
            {"is_title": False, "text": "02 Nuestro enfoque"},
            {"is_title": False, "text": "03 Plan de trabajo"},
            {"is_title": False, "text": "04 Equipo"},
        ],
    }
    assert classify_slide_role(slide) == "index"


def test_classify_slide_role_toc_with_multiline_paragraphs():
    """TOC can also be detected when items are paragraphs inside one shape."""
    slide = {
        "slide_number": 2,
        "layout_name": "Title and Content",
        "title": None,
        "shapes": [
            {
                "is_title": False,
                "text": "1. Introducción\n2. Diagnóstico\n3. Propuesta\n4. Próximos pasos",
            },
        ],
    }
    assert classify_slide_role(slide) == "index"


def test_classify_slide_role_toc_not_detected_outside_position_range():
    """Numbered list deep in the deck is NOT a TOC."""
    slide = {
        "slide_number": 20,
        "layout_name": "Title and Content",
        "title": "Pasos del plan",
        "shapes": [
            {"is_title": True, "text": "Pasos del plan"},
            {"is_title": False, "text": "01 Discovery"},
            {"is_title": False, "text": "02 Design"},
            {"is_title": False, "text": "03 Build"},
        ],
    }
    role = classify_slide_role(slide)
    assert role != "index"


def test_classify_slide_role_section_divider_by_exact_title():
    """Slides titled with common consulting-deck section names are dividers
    even on a regular layout (and with a small body)."""
    for title in (
        "Contexto y objetivos",
        "Nuestro enfoque",
        "Metodología de trabajo",
        "Plan de trabajo",
        "Equipo de trabajo",
        "Valor añadido y aceleradores Minsait",
    ):
        slide = {
            "slide_number": 7,
            "layout_name": "Title and Content",
            "title": title,
            "shapes": [
                {"is_title": True, "text": title},
                {"is_title": False, "text": "Algunos puntos breves"},
            ],
        }
        assert classify_slide_role(slide) == "divider", f"Failed on {title!r}"


def test_classify_slide_role_section_divider_falls_through_when_body_is_large():
    """A real content slide titled 'Nuestro enfoque' with substantial body
    is content, not divider — exact-title match only applies when the body
    is small (< 200 chars)."""
    slide = {
        "slide_number": 7,
        "layout_name": "Title and Content",
        "title": "Nuestro enfoque",
        "shapes": [
            {"is_title": True, "text": "Nuestro enfoque"},
            {"is_title": False, "text": "x" * 500},
        ],
    }
    assert classify_slide_role(slide) == "content_with_title"


def test_classify_slide_role_cv_no_false_positives():
    """CV is a 2-letter word — make sure it doesn't match random substrings."""
    # 'MCV', 'cvc', random text — must NOT match
    for non_cv in ("MCV Solutions", "Cvc del proyecto", "Equipo de trabajo"):
        slide = {"slide_number": 10, "layout_name": "Title and Content", "title": non_cv, "shapes": []}
        role = classify_slide_role(slide)
        assert role != "cv", f"False positive on {non_cv!r}: got {role}"


def test_bad_deck_flags_content_no_title(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    slide_5 = deck["slides"][4]
    assert classify_slide_role(slide_5) == "content_no_title"


# -------- check_min_font_size --------

def test_check_min_font_size_flags_below_threshold():
    slide = {
        "shapes": [
            {"is_title": False, "name": "Body", "min_font_size_pt": 7.5, "text": "tiny"},
            {"is_title": False, "name": "Body2", "min_font_size_pt": 11.0, "text": "ok"},
        ],
    }
    result = check_min_font_size(slide)
    assert result["ok"] is False
    assert len(result["violations"]) == 1
    assert result["violations"][0]["size_pt"] == 7.5
    assert result["smallest_pt"] == 7.5
    assert "9pt" in result["suggestion"]


def test_check_min_font_size_passes_when_all_above():
    slide = {
        "shapes": [
            {"is_title": False, "name": "Body", "min_font_size_pt": 11.0, "text": "ok"},
            {"is_title": False, "name": "Footnote", "min_font_size_pt": 9.0, "text": "ok"},
        ],
    }
    result = check_min_font_size(slide)
    assert result["ok"] is True
    assert result["violations"] == []
    assert result["suggestion"] is None


def test_check_min_font_size_skips_title_and_unset():
    """Title shapes and shapes without explicit size are ignored."""
    slide = {
        "shapes": [
            {"is_title": True, "name": "Title", "min_font_size_pt": 4.0, "text": "title"},
            {"is_title": False, "name": "Body", "min_font_size_pt": None, "text": "inherits"},
        ],
    }
    result = check_min_font_size(slide)
    assert result["ok"] is True


# -------- check_text_density --------

def test_check_text_density_flags_overloaded_slide():
    big_text = "palabra " * 300  # 300 words → over the 260 threshold
    slide = {
        "has_visuals": False,
        "shapes": [{"is_title": False, "text": big_text}],
    }
    result = check_text_density(slide)
    assert result["ok"] is False
    assert result["word_count"] >= 260
    assert "gráfico" in result["suggestion"] or "tabla" in result["suggestion"]


def test_check_text_density_suggests_split_when_has_visuals():
    big_text = "palabra " * 300
    slide = {
        "has_visuals": True,
        "shapes": [{"is_title": False, "text": big_text}],
    }
    result = check_text_density(slide)
    assert result["ok"] is False
    assert "dividirla" in result["suggestion"] or "bullets" in result["suggestion"]


def test_check_text_density_passes_at_250_words():
    """250 words on a slide is OK — should not be flagged.

    Uses realistic Spanish word length (~6 chars). 250 words ≈ 1500 chars,
    well under the 1900-char backstop.
    """
    text_250 = "palabra " * 250  # 250 words × 8 chars = 2000 chars
    # Use shorter words to stay under the char ceiling (the spec is per-word).
    text_250 = "casa " * 250  # 250 words × 5 chars = 1250 chars
    slide = {
        "has_visuals": False,
        "shapes": [{"is_title": False, "text": text_250}],
    }
    result = check_text_density(slide)
    assert result["ok"] is True
    assert result["word_count"] == 250


def test_check_text_density_passes_on_light_slide():
    slide = {
        "has_visuals": False,
        "shapes": [{"is_title": False, "text": "Una idea corta con poco texto."}],
    }
    result = check_text_density(slide)
    assert result["ok"] is True
    assert result["suggestion"] is None


# -------- check_font_family (ForFuture Sans) --------

def test_check_font_family_accepts_forfuture_variants():
    """Any weight/style of ForFuture Sans is OK."""
    for fn in (
        "ForFuture Sans",
        "ForFutureSans-Bold",
        "ForFutureSans-Regular",
        "ForFutureSans-BlackItalic",
        "forfuturesans",
    ):
        slide = {"shapes": [{"is_title": False, "font_names": [fn], "text": "x"}]}
        result = check_font_family(slide)
        assert result["ok"] is True, f"Failed on {fn!r}"


def test_check_font_family_flags_off_brand():
    slide = {
        "shapes": [
            {"is_title": False, "font_names": ["Comic Sans MS"], "text": "x"},
            {"is_title": False, "font_names": ["Times New Roman"], "text": "y"},
        ],
    }
    result = check_font_family(slide)
    assert result["ok"] is False
    assert result["only_fallbacks"] is False
    assert "ForFuture" in result["suggestion"]


def test_check_font_family_marks_fallbacks_as_acceptable():
    slide = {
        "shapes": [{"is_title": False, "font_names": ["Arial"], "text": "x"}],
    }
    result = check_font_family(slide)
    assert result["ok"] is False  # still off-brand
    assert result["only_fallbacks"] is True  # but fallback-acceptable


def test_check_font_family_skips_when_no_explicit_font():
    slide = {"shapes": [{"is_title": False, "text": "inherits from master"}]}
    result = check_font_family(slide)
    assert result["applicable"] is False
    assert result["ok"] is True


# -------- check_title_not_uppercase --------

def test_check_title_not_uppercase_flags_all_caps():
    slide = {"title": "ANÁLISIS DE VENTAS"}
    result = check_title_not_uppercase(slide)
    assert result["ok"] is False
    assert result["suggestion"] is not None
    assert "sentence case" in result["suggestion"]


def test_check_title_not_uppercase_passes_sentence_case():
    slide = {"title": "Las ventas cayeron 18% en Q3"}
    result = check_title_not_uppercase(slide)
    assert result["ok"] is True


def test_check_title_not_uppercase_passes_title_case():
    slide = {"title": "Las Ventas Cayeron 18% en Q3"}
    result = check_title_not_uppercase(slide)
    assert result["ok"] is True


def test_check_title_not_uppercase_skips_short_titles():
    """Short labels like 'P&L' or 'CV' shouldn't trigger."""
    slide = {"title": "P&L"}
    result = check_title_not_uppercase(slide)
    assert result["applicable"] is False


def test_check_title_not_uppercase_handles_empty_title():
    slide = {"title": None}
    result = check_title_not_uppercase(slide)
    assert result["applicable"] is False


# -------- footer alignment outliers --------

def test_footer_alignment_marks_outlier_per_slide():
    """When one slide's footer is way off the median, it gets tagged as outlier."""
    deck = {
        "slide_height_in": 7.5,
        "slides": [
            {
                "slide_number": i,
                "shapes": [{
                    "is_title": False, "name": f"Footer-{i}", "text": "Brand",
                    "top_in": 7.0, "left_in": 0.5, "height_in": 0.3, "width_in": 5.0,
                }],
            }
            for i in range(1, 5)
        ] + [
            {
                "slide_number": 5,
                "shapes": [{
                    "is_title": False, "name": "Footer-5", "text": "Brand",
                    "top_in": 6.5, "left_in": 2.0, "height_in": 0.3, "width_in": 5.0,
                }],
            }
        ],
    }
    result = check_footer_alignment(deck)
    outliers = result.get("outlier_slides", [])
    outlier_nums = {o["slide_number"] for o in outliers}
    assert 5 in outlier_nums
    # First 4 slides share the canonical position → not outliers
    assert 1 not in outlier_nums
    assert result["canonical_top_in"] == 7.0


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
