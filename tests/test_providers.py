"""Tests for the provider abstraction: ClaudeProvider, OpenAIProvider, and the
factory/registry. Uses mocks — no real API calls.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from extractor import extract_deck


# -------- Pricing comparison --------

def test_pricing_table_contains_both_providers():
    from providers import provider_pricing_table
    table = provider_pricing_table()
    assert "claude" in table
    assert "openai" in table
    assert table["claude"]["models"]["per_slide"] == "claude-sonnet-4-6"
    assert table["openai"]["models"]["per_slide"] == "gpt-4o"


def test_compare_providers_for_same_deck():
    from pricing import compare_providers
    comparison = compare_providers(58)
    assert set(comparison) == {"claude", "openai"}
    # OpenAI GPT-4o should be cheaper than Claude (Sonnet+Opus mix) per slide
    assert comparison["openai"]["per_slide_usd"] < comparison["claude"]["per_slide_usd"]


# -------- estimate_cost respects provider arg --------

def test_estimate_cost_per_provider_differs():
    from pricing import estimate_cost
    claude_est = estimate_cost(58, provider="claude")
    openai_est = estimate_cost(58, provider="openai")
    assert claude_est["total_usd"] != openai_est["total_usd"]
    assert claude_est["analyzed_count"] == openai_est["analyzed_count"] == 58


def test_estimate_cost_unknown_provider_raises():
    from pricing import estimate_cost
    with pytest.raises(ValueError):
        estimate_cost(10, provider="grok")


# -------- compute_actual_cost --------

def test_claude_compute_actual_cost():
    from providers import ClaudeProvider
    prov = ClaudeProvider.__new__(ClaudeProvider)  # no SDK init
    usage = {
        "per_slide": {"input": 1_000_000, "output": 100_000, "cache_read": 500_000, "cache_write": 50_000},
        "storyline": {"input": 5000, "output": 5000, "cache_read": 0, "cache_write": 0},
        "visual": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
    }
    cost = prov.compute_actual_cost(usage)
    # Sonnet pricing: $3/$15/$0.30/$3.75
    # input 1M * $3 = $3.00
    # output 100K * $15 = $1.50
    # cache_read 500K * $0.30 = $0.15
    # cache_write 50K * $3.75 = $0.1875
    # per_slide total = $4.8375
    assert cost["per_slide_usd"] == pytest.approx(4.8375, rel=0.01)
    assert cost["provider"] == "claude"
    assert cost["total_usd"] == pytest.approx(cost["per_slide_usd"] + cost["storyline_usd"], rel=0.01)


def test_openai_compute_actual_cost():
    from providers import OpenAIProvider
    prov = OpenAIProvider.__new__(OpenAIProvider)
    usage = {
        "per_slide": {"input": 1_000_000, "output": 100_000, "cache_read": 500_000, "cache_write": 0},
        "storyline": {"input": 5000, "output": 5000, "cache_read": 0, "cache_write": 0},
        "visual": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
    }
    cost = prov.compute_actual_cost(usage)
    # GPT-4o pricing: $2.50/$10/$1.25/$2.50
    # input 1M * $2.50 = $2.50
    # output 100K * $10 = $1.00
    # cache_read 500K * $1.25 = $0.625
    # cache_write 0 = 0
    # per_slide total = $4.125
    assert cost["per_slide_usd"] == pytest.approx(4.125, rel=0.01)
    assert cost["provider"] == "openai"


# -------- OpenAI provider via mock --------

def _build_openai_mock_response(payload: dict) -> SimpleNamespace:
    """Return a SimpleNamespace shaped like an OpenAI ChatCompletion."""
    message = SimpleNamespace(content=json.dumps(payload))
    choice = SimpleNamespace(message=message)
    usage = SimpleNamespace(
        prompt_tokens=600,
        completion_tokens=200,
        prompt_tokens_details=SimpleNamespace(cached_tokens=100),
    )
    return SimpleNamespace(choices=[choice], usage=usage)


@pytest.fixture
def patched_openai(monkeypatch):
    """Patch openai.OpenAI to return a mock client."""
    per_slide_payload = {
        "score": 7,
        "summary": "Mocked OpenAI per-slide.",
        "action_title": {
            "is_action_title": True,
            "current_title": "Mock title",
            "notes": "OK",
            "suggestion": None,
        },
        "so_what": {"present": True, "notes": "OK", "suggestion": None},
        "cause_consequence": {"ok": True, "notes": "OK"},
    }
    storyline_payload = {
        "storyline_coherent": True,
        "storyline_notes": "Mocked OpenAI storyline.",
        "filename_subtitle_alignment": "Mocked.",
        "cross_slide_issues": [],
    }
    visual_payload = {
        "visual_quality": {"ok": True, "notes": "Mocked visual.", "suggestion": None},
        "chart_readability": {"present": True, "ok": True, "notes": "Mocked.", "suggestion": None},
        "design_issues": [],
    }

    def fake_create(**kwargs):
        messages = kwargs.get("messages", [])
        # detect visual by image_url content blocks
        is_visual = any(
            isinstance(b, dict) and b.get("type") == "image_url"
            for m in messages
            for b in (m.get("content", []) if isinstance(m.get("content"), list) else [])
        )
        # storyline differs by schema name in response_format
        schema_name = kwargs.get("response_format", {}).get("json_schema", {}).get("name", "")
        if is_visual:
            payload = visual_payload
        elif schema_name == "StorylineQA":
            payload = storyline_payload
        else:
            payload = per_slide_payload
        return _build_openai_mock_response(payload)

    fake_client = MagicMock()
    fake_client.chat.completions.create = MagicMock(side_effect=fake_create)

    import openai
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: fake_client)
    return fake_client


def _drive_full(generator):
    result = None
    statuses, slide_dones, visual_dones, errors = [], [], [], []
    for kind, payload in generator:
        if kind == "status":
            statuses.append(payload)
        elif kind == "slide_done":
            slide_dones.append(payload)
        elif kind == "visual_done":
            visual_dones.append(payload)
        elif kind == "error":
            errors.append(payload)
        elif kind == "result":
            result = payload
    return result, statuses, slide_dones, visual_dones, errors


def test_full_qa_with_openai_provider(bad_deck_path, patched_openai):
    """Confirm run_full_qa works end-to-end with provider='openai'."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    result, _, slide_dones, _, errors = _drive_full(
        run_full_qa(
            "deck_problemas.pptx", deck,
            api_key="fake-openai-key",
            provider="openai",
        )
    )
    assert not errors
    assert result is not None
    assert result["provider"] == "openai"
    assert result["models"]["per_slide"] == "gpt-4o"
    # The bad deck has 5 slides, all content_no_title/content_with_title (no skip)
    assert len(slide_dones) == 5


def test_actual_cost_in_result(bad_deck_path, patched_openai):
    """After a run, result should include actual_cost computed from observed tokens."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    result, _, _, _, _ = _drive_full(
        run_full_qa("deck_problemas.pptx", deck, api_key="fake-key", provider="openai")
    )
    assert "actual_cost" in result
    ac = result["actual_cost"]
    assert ac["provider"] == "openai"
    assert ac["per_slide_usd"] > 0  # we sent 5 slides
    assert ac["storyline_usd"] > 0


def test_openai_provider_normalizes_usage_correctly(bad_deck_path, patched_openai):
    """Each finding._usage should have input/output/cache_read/cache_write keys."""
    from qa import run_full_qa
    deck = extract_deck(bad_deck_path)
    result, _, _, _, _ = _drive_full(
        run_full_qa("deck_problemas.pptx", deck, api_key="fake-key", provider="openai")
    )
    u = result["usage"]["per_slide"]
    # Mock had prompt_tokens=600, cached=100 → input=500, cache_read=100
    # 5 slides * 500 = 2500 input
    assert u["input"] == 2500
    assert u["cache_read"] == 500
    assert u["output"] == 1000  # 5 * 200
    assert u["cache_write"] == 0  # OpenAI doesn't bill cache writes
