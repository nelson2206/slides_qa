from __future__ import annotations

from extractor import extract_deck
from qa import SEVERITY_ORDER, run_local_qa, severity_for


def _drive(gen):
    result = None
    statuses = []
    for kind, payload in gen:
        if kind == "status":
            statuses.append(payload)
        elif kind == "result":
            result = payload
    return result, statuses


def test_local_qa_runs_with_no_api(bad_deck_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    deck = extract_deck(bad_deck_path)
    result, statuses = _drive(run_local_qa("deck_problemas.pptx", deck))

    assert result is not None
    assert result["mode"] == "local"
    assert len(result["slides"]) == 5
    assert any("determinístico" in s.lower() for s in statuses)


def test_local_qa_flags_bad_deck(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    result, _ = _drive(run_local_qa("deck_problemas.pptx", deck))

    # Slide 2 has long paragraphs
    slide_2 = result["slides"][1]
    assert slide_2["text_length"]["ok"] is False
    assert slide_2["score"] < 10

    # Slide 2 has a footer that's misaligned vs slide 3
    assert slide_2["footer"]["present"] is True
    assert slide_2["footer"]["aligned"] is False

    # Heuristic now judges action_title locally for short titles
    # Slide 2 title is "Análisis de ventas" (3 words) -> verdict False
    assert slide_2["action_title"]["is_action_title"] is False
    assert slide_2["action_title"]["suggestion"] is not None  # has concrete suggestion
    # so_what heuristic returns None (unclear) — no LLM
    # cause_consequence still None (truly needs LLM)
    assert slide_2["cause_consequence"]["ok"] is None

    overview = result["deck_overview"]
    assert overview["mode"] == "local"
    assert overview["storyline_coherent"] is None


def test_local_qa_clean_on_good_deck(good_deck_path):
    deck = extract_deck(good_deck_path)
    result, _ = _drive(run_local_qa("estrategia_comercial_2025.pptx", deck))

    for slide in result["slides"]:
        assert slide["text_length"]["ok"], f"Slide {slide['slide_number']} flagged"
        if slide["footer"]["present"]:
            assert slide["footer"]["aligned"], "Good deck should have aligned footers"

    assert "coincidencias" in result["deck_overview"]["filename_subtitle_alignment"].lower()

    # Footer caps consistent
    caps = result["deck_overview"]["footer_caps_detail"]
    assert caps["applicable"] is True
    assert caps["ok"] is True

    # Footer text consistent (all slides use same footer string)
    text_consistency = result["deck_overview"]["footer_text_consistency_detail"]
    assert text_consistency["ok"] is True

    # Footer matches deck title
    matches = result["deck_overview"]["footer_matches_deck_title_detail"]
    assert matches["applicable"] is True
    assert matches["ok"] is True


def test_local_qa_flags_caps_mismatch_on_bad_deck(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    result, _ = _drive(run_local_qa("deck_problemas.pptx", deck))

    caps = result["deck_overview"]["footer_caps_detail"]
    assert caps["applicable"] is True
    assert caps["ok"] is False

    # The outlier slide should be penalized.
    outlier_slide_nums = {o["slide_number"] for o in caps["outliers"]}
    for slide in result["slides"]:
        if slide["slide_number"] in outlier_slide_nums:
            assert slide["score"] < 10


def test_local_qa_flags_content_no_title(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    result, _ = _drive(run_local_qa("deck_problemas.pptx", deck))

    slide_5 = result["slides"][4]
    assert slide_5["role"] == "content_no_title"
    assert slide_5["score"] <= 7


def test_local_qa_cover_not_penalized_for_no_body_title(good_deck_path):
    deck = extract_deck(good_deck_path)
    result, _ = _drive(run_local_qa("estrategia_comercial_2025.pptx", deck))

    cover = result["slides"][0]
    assert cover["role"] == "cover"
    assert cover["score"] >= 9


def test_local_qa_flags_footer_coverage_gap(bad_deck_path):
    """Slide 4 in the bad fixture has no footer — should be flagged in text consistency."""
    deck = extract_deck(bad_deck_path)
    result, _ = _drive(run_local_qa("deck_problemas.pptx", deck))

    tc = result["deck_overview"]["footer_text_consistency_detail"]
    assert tc["applicable"] is True
    # Bad fixture: only 2 of 3+ content slides have footer
    assert tc["coverage_pct"] < 1.0
    assert tc["ok"] is False


# -------- Severity --------

def test_severity_for_thresholds():
    assert severity_for(0) == "critical"
    assert severity_for(4) == "critical"
    assert severity_for(5) == "warning"
    assert severity_for(7) == "warning"
    assert severity_for(8) == "nit"
    assert severity_for(9) == "nit"
    assert severity_for(10) == "ok"
    # None (skipped) → defaults to nit
    assert severity_for(None) == "nit"


def test_severity_order_constant():
    assert SEVERITY_ORDER == ("critical", "warning", "nit", "ok")


def test_local_qa_emits_severity_per_slide(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    result, _ = _drive(run_local_qa("deck_problemas.pptx", deck))
    for slide in result["slides"]:
        assert "severity" in slide
        assert slide["severity"] in SEVERITY_ORDER
        # Severity should be consistent with score
        assert slide["severity"] == severity_for(slide["score"])


def test_local_qa_severity_distribution_bad_deck(bad_deck_path):
    """Bad fixture should yield at least one critical/warning slide."""
    deck = extract_deck(bad_deck_path)
    result, _ = _drive(run_local_qa("deck_problemas.pptx", deck))
    severities = [s["severity"] for s in result["slides"]]
    # At least one slide is bad enough to be critical or warning
    assert any(s in ("critical", "warning") for s in severities)
