"""Tests for image extraction (#6) and full-mode behavior (#1, #3) with mocks.

These tests do NOT hit the Anthropic API. The Anthropic client is replaced with
a fake that returns canned responses, so we can verify:
- run_full_qa skips configured roles
- run_full_qa yields slide_done events
- Image extraction returns bytes per slide
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from extractor import extract_deck, extract_images


# -------- extractor: image extraction --------

def test_extract_images_returns_bytes(image_deck_path):
    images = extract_images(image_deck_path)
    # The fixture put one picture on slide 2
    assert 2 in images
    assert len(images[2]) == 1
    img_bytes, ext = images[2][0]
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 100  # actual PNG data
    assert ext.lower() in ("png", "jpg", "jpeg")


def test_extract_deck_flags_visual_slide(image_deck_path):
    deck = extract_deck(image_deck_path)
    # slide 1 is the cover (no picture). slide 2 has one picture.
    assert deck["slides"][0]["picture_count"] == 0
    assert deck["slides"][0]["has_visuals"] is False
    assert deck["slides"][1]["picture_count"] == 1
    assert deck["slides"][1]["has_visuals"] is True


def test_extract_images_skips_slides_without_pictures(good_deck_path):
    images = extract_images(good_deck_path)
    # good fixture has no embedded pictures
    assert images == {}


# -------- run_full_qa: skip behavior + slide_done events (mocked) --------

def _make_fake_anthropic_client(per_slide_payload: dict, storyline_payload: dict):
    """Build a mock anthropic.Anthropic that returns canned messages.create() responses.

    Distinguishes between per-slide and storyline calls by checking the model param.
    """
    client = MagicMock()

    def fake_create(**kwargs):
        model = kwargs.get("model", "")
        if "opus" in model:
            payload = storyline_payload
        else:
            payload = per_slide_payload
        text = json.dumps(payload)
        # Build a response object with .content, .usage matching the SDK shape
        content_block = SimpleNamespace(type="text", text=text)
        usage = SimpleNamespace(
            input_tokens=500,
            output_tokens=200,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=100,
        )
        return SimpleNamespace(content=[content_block], usage=usage)

    client.messages.create = MagicMock(side_effect=fake_create)
    return client


@pytest.fixture
def patched_anthropic(monkeypatch):
    """Patch anthropic.Anthropic() to return our mock client."""
    per_slide_payload = {
        "score": 8,
        "summary": "Mocked per-slide finding.",
        "action_title": {
            "is_action_title": True,
            "current_title": "Mock title",
            "notes": "OK",
        },
        "so_what": {"present": True, "notes": "OK"},
        "cause_consequence": {"ok": True, "notes": "OK"},
    }
    storyline_payload = {
        "storyline_coherent": True,
        "storyline_notes": "Mocked storyline.",
        "filename_subtitle_alignment": "Mocked alignment.",
        "cross_slide_issues": [],
    }
    fake_client = _make_fake_anthropic_client(per_slide_payload, storyline_payload)

    # The mock needs to be returned when anthropic.Anthropic(...) is called.
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kwargs: fake_client)
    return fake_client


def _drive_full(generator):
    """Consume the full-mode generator. Return (result, statuses, slide_dones)."""
    result = None
    statuses = []
    slide_dones = []
    visual_dones = []
    errors = []
    for kind, payload in generator:
        if kind == "status":
            statuses.append(payload)
        elif kind == "result":
            result = payload
        elif kind == "slide_done":
            slide_dones.append(payload)
        elif kind == "visual_done":
            visual_dones.append(payload)
        elif kind == "error":
            errors.append(payload)
    return result, statuses, slide_dones, visual_dones, errors


def test_full_qa_skips_default_roles(bad_deck_path, patched_anthropic):
    """Default skip set should exclude divider/minimal slides from Sonnet calls."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    result, _, slide_dones, _, errors = _drive_full(
        run_full_qa("deck_problemas.pptx", deck, api_key="fake-key")
    )
    assert not errors
    assert result is not None
    # Bad deck has slide 5 (no title, blank layout). Slide 5 was classified as
    # content_no_title in earlier tests, NOT minimal, so it WILL be analyzed.
    # The deck has no divider/minimal slides, so analyzed == 5.
    overview = result["deck_overview"]
    # No slides should be skipped because the bad fixture has no divider/minimal
    assert overview["skipped_slides"] == []
    # All 5 should have been sent to Sonnet
    assert len(slide_dones) == 5
    assert overview["analyzed_slides"] == [1, 2, 3, 4, 5]


def test_full_qa_skips_by_role_override(bad_deck_path, patched_anthropic):
    """User can override skip set to skip MORE slides (e.g. content_no_title)."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    # Skip slides classified as content_no_title — slide 5 in the bad fixture.
    result, _, slide_dones, _, _ = _drive_full(
        run_full_qa(
            "deck_problemas.pptx", deck,
            api_key="fake-key",
            skip_roles={"content_no_title"},
        )
    )
    overview = result["deck_overview"]
    assert 5 in overview["skipped_slides"]
    # Only 4 slides sent to Sonnet
    assert len(slide_dones) == 4


def test_full_qa_empty_skip_runs_all(bad_deck_path, patched_anthropic):
    """Passing empty set means: analyze every slide."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    result, _, slide_dones, _, _ = _drive_full(
        run_full_qa("deck_problemas.pptx", deck, api_key="fake-key", skip_roles=set())
    )
    overview = result["deck_overview"]
    assert overview["skipped_slides"] == []
    assert len(slide_dones) == 5


def test_full_qa_slide_done_events_progressive(bad_deck_path, patched_anthropic):
    """slide_done events should arrive one per analyzed slide with completed/total counts."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    _, _, slide_dones, _, _ = _drive_full(
        run_full_qa("deck_problemas.pptx", deck, api_key="fake-key")
    )
    assert len(slide_dones) == 5
    # 'completed' field should increment
    completeds = [s["completed"] for s in slide_dones]
    assert completeds == sorted(completeds)
    assert completeds[-1] == 5
    assert all(s["total"] == 5 for s in slide_dones)


def test_full_qa_visual_disabled_by_default(bad_deck_path, patched_anthropic):
    """No visual_done events when visual_analysis=False (default)."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    _, _, _, visual_dones, _ = _drive_full(
        run_full_qa("deck_problemas.pptx", deck, api_key="fake-key")
    )
    assert visual_dones == []


def test_full_qa_visual_runs_when_enabled(image_deck_path, patched_anthropic):
    """When visual_analysis=True and images are passed, visual_done events fire."""
    from qa import run_full_qa
    deck = extract_deck(image_deck_path)
    images = extract_images(image_deck_path)

    # Patch the per-slide and storyline payloads work for both calls.
    # Visual schema is different — need a separate mock that detects "image" content.
    # Existing mock returns the per-slide schema for any non-Opus model. The visual
    # call uses Opus. Need to extend the mock.

    import anthropic
    visual_payload = {
        "visual_quality": {"ok": True, "notes": "Mocked visual."},
        "chart_readability": {"present": True, "ok": True, "notes": "Mocked chart."},
        "design_issues": [],
    }
    storyline_payload = {
        "storyline_coherent": True,
        "storyline_notes": "Mocked storyline.",
        "filename_subtitle_alignment": "Mocked.",
        "cross_slide_issues": [],
    }
    per_slide_payload = {
        "score": 8, "summary": "Mocked.",
        "action_title": {"is_action_title": True, "current_title": "T", "notes": "OK"},
        "so_what": {"present": True, "notes": "OK"},
        "cause_consequence": {"ok": True, "notes": "OK"},
    }

    def fake_create(**kwargs):
        model = kwargs.get("model", "")
        messages = kwargs.get("messages", [])
        # Detect visual call by checking for image content blocks
        is_visual = any(
            isinstance(b, dict) and b.get("type") == "image"
            for m in messages
            for b in (m.get("content", []) if isinstance(m.get("content"), list) else [])
        )
        if is_visual:
            payload = visual_payload
        elif "opus" in model:
            payload = storyline_payload
        else:
            payload = per_slide_payload
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps(payload))],
            usage=SimpleNamespace(
                input_tokens=500, output_tokens=200,
                cache_read_input_tokens=0, cache_creation_input_tokens=100,
            ),
        )

    fake_client = MagicMock()
    fake_client.messages.create = MagicMock(side_effect=fake_create)

    import qa  # ensure module is loaded
    anthropic.Anthropic = lambda **kwargs: fake_client

    result, _, _, visual_dones, _ = _drive_full(
        run_full_qa(
            image_deck_path.name, deck, api_key="fake-key",
            visual_analysis=True, images_by_slide=images,
        )
    )

    # Slide 2 has an image -> exactly 1 visual_done event
    assert len(visual_dones) == 1
    assert visual_dones[0]["slide_number"] == 2
    # Visual finding propagates into the per-slide result
    slide_2 = next(s for s in result["slides"] if s["slide_number"] == 2)
    assert "visual" in slide_2
    assert slide_2["visual"]["visual_quality"]["ok"] is True
    # Deck overview reports visual usage was enabled
    assert result["deck_overview"]["visual_analysis_enabled"] is True
    assert 2 in result["deck_overview"]["visual_slides"]


def test_full_qa_includes_skipped_in_final_report(image_deck_path, patched_anthropic):
    """Skipped slides should still appear in result['slides'] with role + deterministic data."""
    from qa import run_full_qa
    deck = extract_deck(image_deck_path)
    # Image deck slide 2 has layout 'Title Only', which contains 'title only' hint
    # -> classified as divider -> default skipped. Slide 1 is cover (analyzed).
    result, _, slide_dones, _, _ = _drive_full(
        run_full_qa(image_deck_path.name, deck, api_key="fake-key")
    )
    overview = result["deck_overview"]
    # Slide 2 should be skipped (divider layout)
    assert 2 in overview["skipped_slides"]
    # Only slide 1 (cover) goes to Sonnet
    assert len(slide_dones) == 1
    # Skipped slide is still in the final report
    assert len(result["slides"]) == 2
    slide_2 = next(s for s in result["slides"] if s["slide_number"] == 2)
    assert slide_2.get("_skipped") is True


# -------- pricing: skip + visual --------

def test_pricing_skip_reduces_cost():
    from pricing import estimate_cost
    full = estimate_cost(58)
    skipped = estimate_cost(58, skipped_count=10)
    assert skipped["sonnet_usd"] < full["sonnet_usd"]
    assert skipped["analyzed_count"] == 48
    # Opus storyline cost should be unchanged
    assert skipped["opus_storyline_usd"] == full["opus_storyline_usd"]


def test_pricing_visual_adds_cost():
    from pricing import estimate_cost
    no_vis = estimate_cost(58)
    with_vis = estimate_cost(58, visual_slide_count=12)
    assert with_vis["opus_visual_usd"] > 0
    assert with_vis["total_usd"] > no_vis["total_usd"]


def test_pricing_backward_compat_keys():
    """Old code paths expect 'opus_usd' and 'total_usd' keys."""
    from pricing import estimate_cost
    est = estimate_cost(58)
    assert "opus_usd" in est
    assert "total_usd" in est
