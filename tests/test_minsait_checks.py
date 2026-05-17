"""Tests for the Minsait playbook linguistic checks (page 26).

Covers the 6 new checks introduced to operationalize the Minsait
"Presentaciones estructuradas" training deck:

  1. check_bullet_parallelism      — first-word POS consistency in bullets
  2. check_action_verbs_in_bullets — binding verbs (ser/estar/tener) flagged
  3. check_anglicisms              — anglicisms must be italic per page 26
  4. check_bold_consistency        — bold emphasis homogeneous (numeric vs text)
  5. check_kicker                  — supertítulo / eyebrow tag detection
  6. check_slide_type_label        — preliminar / backup / discusión tags
"""

from __future__ import annotations

from checks import (
    check_action_verbs_in_bullets,
    check_anglicism_consistency,
    check_anglicisms,
    check_bold_consistency,
    check_bullet_parallelism,
    check_kicker,
    check_kicker_consistency,
    check_slide_type_label,
    check_slide_type_label_summary,
)


# -------- bullet parallelism --------

def test_parallelism_all_verbs_ok():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"text": "Definir el modelo de atencion"},
                    {"text": "Implementar el roadmap tecnologico"},
                    {"text": "Evaluar el ROI trimestral"},
                    {"text": "Optimizar los costes variables"},
                ],
            }
        ]
    }
    r = check_bullet_parallelism(slide)
    assert r["ok"] is True


def test_parallelism_mixed_flagged():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"text": "Optimizar el modelo"},
                    {"text": "Reduccion de costes"},
                    {"text": "Definir estrategia"},
                    {"text": "Estrategia de canal"},
                ],
            }
        ]
    }
    r = check_bullet_parallelism(slide)
    assert r["applicable"] is True
    assert r["ok"] is False
    assert len(r["findings"]) == 1
    assert r["findings"][0]["bullet_count"] == 4


def test_parallelism_too_few_bullets_skipped():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"text": "Optimizar X"},
                    {"text": "Reduccion Y"},
                ],
            }
        ]
    }
    r = check_bullet_parallelism(slide)
    assert r["applicable"] is False


# -------- action verbs vs binding verbs --------

def test_binding_verbs_dominant_flagged():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"text": "Es necesario revisar el modelo"},
                    {"text": "Son criticos los KPIs"},
                    {"text": "Esta pendiente la auditoria"},
                    {"text": "Tiene un impacto significativo"},
                ],
            }
        ]
    }
    r = check_action_verbs_in_bullets(slide)
    assert r["ok"] is False
    assert r["findings"][0]["binding_ratio"] >= 0.5


def test_action_verbs_dominant_ok():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"text": "Optimizar procesos"},
                    {"text": "Implementar el roadmap"},
                    {"text": "Evaluar resultados"},
                ],
            }
        ]
    }
    r = check_action_verbs_in_bullets(slide)
    assert r["ok"] is True


# -------- anglicisms --------

def test_anglicism_without_italic_flagged():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {
                        "text": "Definir el roadmap del proyecto",
                        "runs": [
                            {"text": "Definir el ", "bold": None, "italic": None},
                            {"text": "roadmap", "bold": None, "italic": False},
                            {"text": " del proyecto", "bold": None, "italic": None},
                        ],
                    }
                ],
            }
        ]
    }
    r = check_anglicisms(slide)
    assert r["ok"] is False
    assert len(r["findings"]) == 1
    assert r["findings"][0]["term"] == "roadmap"


def test_anglicism_with_italic_ok():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {
                        "text": "Definir el roadmap",
                        "runs": [
                            {"text": "Definir el ", "bold": None, "italic": False},
                            {"text": "roadmap", "bold": None, "italic": True},
                        ],
                    }
                ],
            }
        ]
    }
    r = check_anglicisms(slide)
    assert r["applicable"] is True
    assert r["ok"] is True
    assert len(r["correct_italic"]) == 1


def test_anglicism_no_anglicisms_not_applicable():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {
                        "text": "Definir la hoja de ruta del proyecto",
                        "runs": [
                            {"text": "Definir la hoja de ruta", "bold": None, "italic": False},
                        ],
                    }
                ],
            }
        ]
    }
    r = check_anglicisms(slide)
    assert r["applicable"] is False


def test_anglicism_consistency_deck_rollup():
    deck = {
        "slides": [
            {
                "slide_number": 1,
                "shapes": [
                    {"name": "body", "is_title": False, "paragraphs": [
                        {"runs": [{"text": "El roadmap define", "bold": None, "italic": False}]},
                    ]}
                ],
            },
            {
                "slide_number": 2,
                "shapes": [
                    {"name": "body", "is_title": False, "paragraphs": [
                        {"runs": [{"text": "stakeholder principal", "bold": None, "italic": False}]},
                    ]}
                ],
            },
        ]
    }
    r = check_anglicism_consistency(deck)
    assert r["applicable"] is True
    assert r["non_italic_uses"] == 2
    assert r["italic_uses"] == 0
    assert 1 in r["offending_slides"]
    assert 2 in r["offending_slides"]


# -------- bold consistency --------

def test_bold_all_numeric_ok():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"runs": [
                        {"text": "Crecimiento de ", "bold": False, "italic": None},
                        {"text": "30%", "bold": True, "italic": None},
                    ]},
                    {"runs": [
                        {"text": "Reduccion de costes de ", "bold": False, "italic": None},
                        {"text": "$5M", "bold": True, "italic": None},
                    ]},
                    {"runs": [
                        {"text": "ROI de ", "bold": False, "italic": None},
                        {"text": "12%", "bold": True, "italic": None},
                    ]},
                ],
            }
        ]
    }
    r = check_bold_consistency(slide)
    assert r["ok"] is True
    assert r["dominant_class"] == "numeric"


def test_bold_mixed_flagged():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"runs": [{"text": "30%", "bold": True, "italic": None}]},
                    {"runs": [{"text": "$5M", "bold": True, "italic": None}]},
                    {"runs": [{"text": "optimizacion", "bold": True, "italic": None}]},
                    {"runs": [{"text": "transformacion digital", "bold": True, "italic": None}]},
                ],
            }
        ]
    }
    r = check_bold_consistency(slide)
    assert r["ok"] is False


def test_bold_too_few_skipped():
    slide = {
        "shapes": [
            {
                "name": "body", "is_title": False,
                "paragraphs": [
                    {"runs": [{"text": "30%", "bold": True, "italic": None}]},
                ],
            }
        ]
    }
    r = check_bold_consistency(slide)
    assert r["applicable"] is False


# -------- kicker / supertitulo --------

def test_kicker_detected():
    slide = {
        "shapes": [
            {
                "is_title": False, "name": "kicker",
                "text": "Capitulo 02 - Analisis",
                "top_in": 0.3, "height_in": 0.3, "min_font_size_pt": 10.0,
                "paragraphs": [{"text": "Capitulo 02 - Analisis"}],
            },
            {
                "is_title": True, "name": "title",
                "text": "Las ventas crecieron 18%",
                "top_in": 0.8, "height_in": 0.6, "min_font_size_pt": 22.0,
                "paragraphs": [{"text": "Las ventas crecieron 18%"}],
            },
        ]
    }
    r = check_kicker(slide)
    assert r["present"] is True
    assert "kicker_text" in r


def test_kicker_no_kicker():
    slide = {
        "shapes": [
            {
                "is_title": True, "name": "title",
                "text": "Las ventas crecieron",
                "top_in": 0.5, "height_in": 0.6, "min_font_size_pt": 22.0,
                "paragraphs": [{"text": "Las ventas crecieron"}],
            },
        ]
    }
    r = check_kicker(slide)
    assert r["present"] is False


# -------- slide type labels --------

def test_slide_type_label_preliminar_detected():
    slide = {
        "shapes": [
            {
                "text": "Preliminar - discusion interna", "name": "tag",
                "paragraphs": [{"text": "Preliminar"}],
            }
        ]
    }
    r = check_slide_type_label(slide)
    assert r["present"] is True
    assert "preliminar" in r["labels"]


def test_slide_type_label_backup_detected():
    slide = {
        "shapes": [
            {"text": "Backup", "name": "tag", "paragraphs": [{"text": "Backup"}]},
        ]
    }
    r = check_slide_type_label(slide)
    assert r["present"] is True
    assert "backup" in r["labels"]


def test_slide_type_label_summary_rollup():
    deck = {
        "slides": [
            {"slide_number": 1, "shapes": [
                {"text": "Preliminar", "paragraphs": [{"text": "P"}]}
            ]},
            {"slide_number": 5, "shapes": [
                {"text": "Backup", "paragraphs": [{"text": "B"}]}
            ]},
            {"slide_number": 6, "shapes": [
                {"text": "Backup", "paragraphs": [{"text": "B"}]}
            ]},
        ]
    }
    r = check_slide_type_label_summary(deck)
    assert r["present"] is True
    assert "preliminar" in r["by_label"]
    assert "backup" in r["by_label"]
    assert r["by_label"]["backup"] == [5, 6]


# -------- best_practices_html v2 smoke test --------

def test_best_practices_html_v2_smoke():
    """The redesigned panel renders without errors and contains all 3 pillars."""
    from styles import best_practices_html
    html = best_practices_html()
    # Must include all 3 pillar anchors
    assert 'id="qa-bp-pillar-1"' in html
    assert 'id="qa-bp-pillar-2"' in html
    assert 'id="qa-bp-pillar-3"' in html
    # Hero tiles
    assert "qa-bp-hero-tile" in html
    # Pyramid SVG
    assert "qaPyrTop" in html
    # SCQR flow + audience matrix
    assert "qa-bp-scqr-block" in html
    assert "Alta dirección" in html
    assert "Mando medio" in html
    # Chart picker tabs
    assert "qa-bp-chart-tabs" in html
    # Quality gate (3 columns)
    assert html.count("qa-bp-qgate-col") == 3
    # No leftover Python f-string artifacts (suspicious .split() residue)
    assert "</div></div></div></div></div></div>" not in html
