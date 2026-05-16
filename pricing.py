"""Cost estimation — delegates to provider classes.

Kept as a thin module for backwards-compat with existing CLI scripts and tests.
The actual pricing constants live in `providers.py` on each Provider subclass.
"""

from __future__ import annotations

from providers import PROVIDERS


def estimate_cost(
    slide_count: int,
    *,
    skipped_count: int = 0,
    visual_slide_count: int = 0,
    visual_images_total: int | None = None,
    provider: str = "claude",
) -> dict:
    """Order-of-magnitude estimate. Real billing may differ ±30%."""
    if slide_count <= 0:
        return {
            "slide_count": 0,
            "analyzed_count": 0,
            "skipped_count": 0,
            "sonnet_usd": 0.0,
            "opus_storyline_usd": 0.0,
            "opus_visual_usd": 0.0,
            "opus_usd": 0.0,
            "total_usd": 0.0,
            "per_slide_usd": 0.0,
            "storyline_usd": 0.0,
            "visual_usd": 0.0,
        }

    cls = PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider!r}")
    inst = cls.__new__(cls)  # avoid __init__ (which connects to the SDK)

    est = inst.estimate_cost(
        slide_count,
        skipped_count=skipped_count,
        visual_slide_count=visual_slide_count,
    )

    # Backward-compat aliases for existing callers (CLI scripts, old tests).
    est["sonnet_usd"] = est["per_slide_usd"]
    est["opus_storyline_usd"] = est["storyline_usd"]
    est["opus_visual_usd"] = est["visual_usd"]
    est["opus_usd"] = est["storyline_usd"] + est["visual_usd"]
    return est


def compare_providers(
    slide_count: int,
    *,
    skipped_count: int = 0,
    visual_slide_count: int = 0,
) -> dict[str, dict]:
    """Return cost estimates side-by-side for every registered provider."""
    return {
        name: estimate_cost(
            slide_count,
            skipped_count=skipped_count,
            visual_slide_count=visual_slide_count,
            provider=name,
        )
        for name in PROVIDERS
    }
