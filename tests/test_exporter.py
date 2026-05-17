from __future__ import annotations

import io

import pytest
from pptx import Presentation

from exporter import (
    apply_quick_fixes,
    available_fixes_for_slide,
    export_annotated_pptx,
)


# ---------- annotated export ----------

def _fake_result(slide_numbers: list[int]) -> dict:
    """Minimal result dict shape for export tests."""
    slides = []
    for n in slide_numbers:
        slides.append({
            "slide_number": n,
            "role": "content_with_title",
            "score": 6,
            "severity": "warning",
            "summary": f"Slide {n} test summary.",
            "_skipped": False,
            "action_title": {
                "is_action_title": False,
                "current_title": f"Title {n}",
                "notes": "Solo descriptivo.",
                "suggestion": f"Las ventas {n} cayeron 18%.",
            },
            "so_what": {
                "present": False,
                "notes": "Falta implicación.",
                "suggestion": "Agregar qué decisión habilita.",
            },
            "cause_consequence": {"ok": True, "notes": "OK"},
            "text_length": {"ok": True, "long_paragraphs": [], "notes": "OK", "suggestion": None},
            "footer": {
                "present": True,
                "current_footer": "Footer wrong",
                "aligned": True,
                "matches_canonical": False,
                "canonical_text": "Minsait · 2026",
                "exempt": False,
                "alignment_outlier": None,
                "notes": "—",
            },
            "title_case": {
                "applicable": True,
                "ok": False,
                "title": f"TITLE {n}",
                "case_violation": "all_caps",
                "notes": "MAYÚSCULAS",
                "suggestion": f'Reescribir en sentence case: "Title {n}".',
            },
            "font_family": {"applicable": True, "ok": True, "notes": "OK"},
            "min_font_size": {"applicable": True, "ok": True, "notes": "OK"},
            "text_density": {"applicable": True, "ok": True, "notes": "OK"},
        })
    return {
        "mode": "local",
        "slides": slides,
        "deck_overview": {
            "storyline_coherent": False,
            "storyline_notes": "Falta governing thought.",
            "filename_subtitle_alignment": "Filename no matchea.",
            "cross_slide_issues": [
                {"slide_numbers": [1, 2], "issue": "S1 y S2 invertidos."},
            ],
        },
    }


def test_export_annotated_pptx_writes_notes_and_summary_slide(bad_deck_path):
    deck = Presentation(str(bad_deck_path))
    original_slide_count = len(deck.slides)
    result = _fake_result(list(range(1, original_slide_count + 1)))

    out_bytes = export_annotated_pptx(str(bad_deck_path), result)
    assert len(out_bytes) > 0

    out_deck = Presentation(io.BytesIO(out_bytes))
    # +1 because of the summary slide appended at the end
    assert len(out_deck.slides) == original_slide_count + 1

    # Speaker notes on every existing slide should contain Holmes' block
    for i, slide in enumerate(out_deck.slides):
        if i == original_slide_count:
            break  # skip the summary slide we appended
        notes_text = slide.notes_slide.notes_text_frame.text
        assert "HOLMES REVIEW" in notes_text, f"Slide {i+1} missing Holmes notes"

    # Summary slide title
    summary_slide = out_deck.slides[-1]
    if summary_slide.shapes.title is not None:
        assert summary_slide.shapes.title.text == "Holmes Review"


def test_export_annotated_pptx_preserves_existing_notes(bad_deck_path):
    """Existing speaker notes should survive — Holmes' block is appended."""
    deck = Presentation(str(bad_deck_path))
    deck.slides[0].notes_slide.notes_text_frame.text = "Notas previas del consultor"
    modified_path = str(bad_deck_path) + ".modified.pptx"
    deck.save(modified_path)

    result = _fake_result([1])
    out_bytes = export_annotated_pptx(modified_path, result)
    out_deck = Presentation(io.BytesIO(out_bytes))
    notes = out_deck.slides[0].notes_slide.notes_text_frame.text
    assert "Notas previas del consultor" in notes
    assert "HOLMES REVIEW" in notes


# ---------- auto-fix engine ----------

def test_available_fixes_for_slide_lists_actionable_fixes():
    finding = {
        "slide_number": 3,
        "_skipped": False,
        "title_case": {
            "applicable": True,
            "ok": False,
            "title": "ANÁLISIS DE VENTAS",
            "case_violation": "all_caps",
        },
        "action_title": {
            "is_action_title": False,
            "current_title": "Análisis de ventas",
            "suggestion": "Las ventas cayeron 18% en Q3.",
        },
        "footer": {
            "present": True,
            "current_footer": "Wrong",
            "matches_canonical": False,
            "canonical_text": "Minsait · 2026",
            "exempt": False,
        },
    }
    fixes = available_fixes_for_slide(finding)
    ids = [f["id"] for f in fixes]
    assert "sentence_case_title" in ids
    assert "apply_llm_action_title" in ids
    assert "canonical_footer_text" in ids
    assert all(f["slide_number"] == 3 for f in fixes)


def test_available_fixes_for_slide_skips_skipped_slides():
    finding = {"slide_number": 1, "_skipped": True, "title_case": {"applicable": True, "ok": False}}
    assert available_fixes_for_slide(finding) == []


def test_available_fixes_for_slide_skips_when_no_diff():
    """If sentence-case version equals the original, don't offer the fix."""
    finding = {
        "slide_number": 2,
        "_skipped": False,
        "title_case": {
            "applicable": True,
            "ok": False,
            "title": "Already sentence case",
            "case_violation": "title_case",
        },
        "action_title": {},
        "footer": {},
    }
    fixes = available_fixes_for_slide(finding)
    # "Already sentence case" → _to_sentence_case → "Already sentence case" → no diff
    # (capitalized first, rest lowered; "already" → "Already" + "sentence" + "case" = "Already sentence case")
    ids = [f["id"] for f in fixes]
    assert "sentence_case_title" not in ids


def test_apply_quick_fixes_rewrites_title_text(good_deck_path):
    """Apply a sentence_case_title fix and verify the title text changed."""
    fix = {
        "id": "sentence_case_title",
        "slide_number": 2,
        "label": "Convertir título a sentence case",
        "preview_before": "ORIGINAL",
        "preview_after": "Sentence case title",
    }
    out_bytes, report = apply_quick_fixes(str(good_deck_path), {"slides": []}, [fix])
    assert report["counts"]["applied"] == 1
    assert report["counts"]["failed"] == 0

    out_deck = Presentation(io.BytesIO(out_bytes))
    slide_2 = out_deck.slides[1]
    if slide_2.shapes.title is not None:
        assert slide_2.shapes.title.text == "Sentence case title"


def test_apply_quick_fixes_reports_failures_gracefully(good_deck_path):
    """Asking to fix a slide that doesn't exist should fail cleanly, not crash."""
    fix = {
        "id": "sentence_case_title",
        "slide_number": 999,
        "preview_before": "X",
        "preview_after": "Y",
    }
    out_bytes, report = apply_quick_fixes(str(good_deck_path), {"slides": []}, [fix])
    assert report["counts"]["applied"] == 0
    assert report["counts"]["failed"] == 1
    assert "no encontrada" in report["failed"][0]["reason"].lower()
    # PPTX should still be returned (unmodified)
    out_deck = Presentation(io.BytesIO(out_bytes))
    assert len(out_deck.slides) > 0
