from __future__ import annotations

from extractor import extract_deck


def test_extractor_basic_shape(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    assert deck["slide_count"] == 5
    assert deck["slide_width_in"] is not None
    assert deck["slide_height_in"] is not None
    assert len(deck["slides"]) == 5


def test_extractor_captures_titles_and_paragraphs(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    titles = [s["title"] for s in deck["slides"]]
    assert titles[0] == "Resultados 2024"
    assert titles[1] == "Análisis de ventas"

    body = deck["slides"][1]["shapes"]
    assert any("ventas" in (s.get("text") or "").lower() for s in body)


def test_extractor_captures_footer_shape(bad_deck_path):
    deck = extract_deck(bad_deck_path)
    slide_2 = deck["slides"][1]
    # The footer textbox sits at the bottom; pptx will have it as a non-placeholder shape.
    footer_box = next((s for s in slide_2["shapes"] if s["text"] == "Estudio 2024"), None)
    assert footer_box is not None
    assert footer_box["top_in"] is not None
    assert footer_box["height_in"] is not None
    assert not footer_box["is_title"]
    # Footer is in the bottom area of the 7.5" slide
    assert footer_box["top_in"] >= 6.5


def test_extractor_good_deck_has_action_titles(good_deck_path):
    deck = extract_deck(good_deck_path)
    titles = [s["title"] or "" for s in deck["slides"]]
    # Good-deck titles are long action statements (~50+ chars)
    for t in titles[1:]:  # skip cover
        assert len(t) > 40, f"Action titles should be substantive, got: {t!r}"
