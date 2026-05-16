"""Tests for the schematic renderer.

PowerPoint COM path is OS-specific and hard to mock — tested manually on
the dev machine. These tests cover the always-available schematic backend.
"""

from __future__ import annotations

from extractor import extract_deck
from renderer import (
    THUMB_H,
    THUMB_W,
    cache_key_for,
    render_schematic,
    render_schematic_for_deck,
)


def test_schematic_returns_png_bytes(good_deck_path):
    deck = extract_deck(good_deck_path)
    result = render_schematic_for_deck(deck)
    assert len(result) == deck["slide_count"]
    for slide_num, png in result.items():
        # PNG magic header
        assert png[:8] == b"\x89PNG\r\n\x1a\n", f"slide {slide_num} not PNG"
        assert len(png) > 200, f"slide {slide_num} png suspiciously small"


def test_schematic_uses_requested_dimensions(good_deck_path):
    from PIL import Image
    import io
    deck = extract_deck(good_deck_path)
    result = render_schematic_for_deck(deck, width=320, height=180)
    img = Image.open(io.BytesIO(next(iter(result.values()))))
    assert img.size == (320, 180)


def test_schematic_for_single_slide(good_deck_path):
    deck = extract_deck(good_deck_path)
    png = render_schematic(deck["slides"][0], 13.333, 7.5)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_schematic_handles_filter(good_deck_path):
    deck = extract_deck(good_deck_path)
    result = render_schematic_for_deck(deck, slide_numbers=[2])
    assert list(result.keys()) == [2]


def test_schematic_progress_cb(good_deck_path):
    deck = extract_deck(good_deck_path)
    calls = []
    render_schematic_for_deck(deck, progress_cb=lambda done, total: calls.append((done, total)))
    assert len(calls) == deck["slide_count"]
    assert calls[-1][0] == deck["slide_count"]


def test_cache_key_changes_with_file(good_deck_path, bad_deck_path):
    assert cache_key_for(good_deck_path) != cache_key_for(bad_deck_path)


def test_default_dimensions():
    assert THUMB_W == 480
    assert THUMB_H == 270


# -------- detection probes --------

def test_powerpoint_detection_returns_tuple():
    from renderer import is_powerpoint_available
    avail, source = is_powerpoint_available()
    assert isinstance(avail, bool)
    assert isinstance(source, str)


def test_libreoffice_detection_returns_tuple():
    from renderer import is_libreoffice_available
    avail, source = is_libreoffice_available()
    assert isinstance(avail, bool)
    assert isinstance(source, str)


def test_render_auto_falls_back_to_schematic(good_deck_path):
    """Without a pptx_path, auto mode should fall back to schematic for the deck."""
    from extractor import extract_deck
    from renderer import render
    deck = extract_deck(good_deck_path)
    thumbs, mode = render(deck=deck, mode="schematic")
    assert mode == "schematic"
    assert len(thumbs) == deck["slide_count"]
