"""Provider abstraction for the QA pipeline.

Two providers supported:
- ClaudeProvider: Anthropic Claude (Sonnet 4.6 for per-slide, Opus 4.7 for storyline/visual)
- OpenAIProvider: OpenAI (GPT-4o for everything)

Each provider implements:
- analyze_slide(slide, file_name)        -> per-slide JSON finding
- analyze_storyline(file_name, deck, findings) -> deck-level JSON
- analyze_visual(slide_number, images, title, body) -> visual JSON
- pricing                                 -> dict of $/1M tokens by stage

Cost computation:
- estimate_cost(slide_count, ...)         -> projected $ before running
- compute_actual_cost(usage_breakdown)    -> real $ from observed token counts
"""

from __future__ import annotations

import base64
import json
import os
from abc import ABC, abstractmethod
from typing import Any

from prompts import (
    PER_SLIDE_SCHEMA,
    PER_SLIDE_SYSTEM,
    STORYLINE_SCHEMA,
    STORYLINE_SYSTEM,
    VISUAL_SCHEMA,
    VISUAL_SYSTEM,
)


def _normalize_usage_anthropic(usage: Any) -> dict[str, int]:
    return {
        "input": int(getattr(usage, "input_tokens", 0) or 0),
        "output": int(getattr(usage, "output_tokens", 0) or 0),
        "cache_read": int(getattr(usage, "cache_read_input_tokens", 0) or 0),
        "cache_write": int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
    }


def _normalize_usage_openai(usage: Any) -> dict[str, int]:
    """OpenAI returns prompt_tokens (total) + nested cached_tokens.

    For consistency with Anthropic, we split into uncached input and cached input.
    cache_write is always 0 (OpenAI doesn't bill separately for cache writes).
    """
    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    details = getattr(usage, "prompt_tokens_details", None)
    cached = 0
    if details is not None:
        cached = int(getattr(details, "cached_tokens", 0) or 0)
    return {
        "input": max(0, prompt - cached),
        "output": completion,
        "cache_read": cached,
        "cache_write": 0,
    }


def _build_slide_user_message(slide: dict[str, Any], file_name: str) -> str:
    body_text = "\n\n".join(
        sh["text"] for sh in slide.get("shapes", [])
        if not sh.get("is_title") and sh.get("text")
    )
    return (
        f"Archivo: {file_name}\n"
        f"Slide número: {slide['slide_number']}\n"
        f"Título: {slide.get('title') or '(sin título)'}\n"
        f"Cuerpo:\n{body_text or '(vacío)'}"
    )


def _build_storyline_digest(file_name: str, deck: dict[str, Any], findings: list[dict]) -> str:
    lines = [f"Archivo: {file_name}", f"Slides totales: {deck['slide_count']}", ""]
    for slide, finding in zip(deck["slides"], findings):
        n = slide["slide_number"]
        title = slide.get("title") or "(sin título)"
        lines.append(f"Slide {n} | título: {title}")
        lines.append(f"  summary: {finding.get('summary', '')}")
    return "\n".join(lines)


# ===========================================================================
# Base provider
# ===========================================================================

class Provider(ABC):
    """Abstract base for QA providers."""

    name: str = "abstract"
    per_slide_model: str = ""
    storyline_model: str = ""
    visual_model: str = ""

    # Pricing in USD per 1M tokens. Each entry: {input, output, cache_read, cache_write}.
    pricing_per_slide: dict[str, float] = {}
    pricing_storyline: dict[str, float] = {}
    pricing_visual: dict[str, float] = {}

    @abstractmethod
    def analyze_slide(self, slide: dict[str, Any], file_name: str) -> dict[str, Any]: ...

    @abstractmethod
    def analyze_storyline(
        self, file_name: str, deck: dict[str, Any], findings: list[dict[str, Any]]
    ) -> dict[str, Any]: ...

    @abstractmethod
    def analyze_visual(
        self,
        slide_number: int,
        images: list[tuple[bytes, str]],
        slide_title: str,
        body_text: str,
    ) -> dict[str, Any]: ...

    # ------ Cost helpers ------

    def estimate_cost(
        self,
        slide_count: int,
        *,
        skipped_count: int = 0,
        visual_slide_count: int = 0,
        per_slide_input_tokens: int = 1500,
        per_slide_output_tokens: int = 500,
        cached_system_tokens: int = 700,
        opus_storyline_in: int = 5000,
        opus_storyline_out: int = 5000,
        visual_input_per_image: int = 2500,
        visual_output_per_slide: int = 800,
    ) -> dict[str, Any]:
        analyzed = max(0, slide_count - skipped_count)
        # Per-slide (cached system prompt: 1 write + N-1 reads)
        per = self.pricing_per_slide
        ps_in_m = analyzed * per_slide_input_tokens / 1_000_000
        ps_out_m = analyzed * per_slide_output_tokens / 1_000_000
        ps_cw_m = (cached_system_tokens / 1_000_000) if analyzed > 0 else 0
        ps_cr_m = cached_system_tokens * max(0, analyzed - 1) / 1_000_000
        per_slide_usd = (
            ps_in_m * per["input"]
            + ps_out_m * per["output"]
            + ps_cw_m * per["cache_write"]
            + ps_cr_m * per["cache_read"]
        )

        # Storyline
        sl = self.pricing_storyline
        sl_in_m = opus_storyline_in / 1_000_000
        sl_out_m = opus_storyline_out / 1_000_000
        storyline_usd = sl_in_m * sl["input"] + sl_out_m * sl["output"]

        # Visual
        vis_usd = 0.0
        if visual_slide_count > 0:
            v = self.pricing_visual
            v_in_m = (visual_slide_count * 200 + visual_slide_count * visual_input_per_image) / 1_000_000
            v_out_m = visual_slide_count * visual_output_per_slide / 1_000_000
            vis_usd = v_in_m * v["input"] + v_out_m * v["output"]

        return {
            "provider": self.name,
            "slide_count": slide_count,
            "analyzed_count": analyzed,
            "skipped_count": skipped_count,
            "per_slide_usd": per_slide_usd,
            "storyline_usd": storyline_usd,
            "visual_usd": vis_usd,
            "total_usd": per_slide_usd + storyline_usd + vis_usd,
            "models": {
                "per_slide": self.per_slide_model,
                "storyline": self.storyline_model,
                "visual": self.visual_model,
            },
        }

    @staticmethod
    def _stage_cost(usage: dict[str, int], pricing: dict[str, float]) -> float:
        return (
            usage.get("input", 0) / 1_000_000 * pricing["input"]
            + usage.get("output", 0) / 1_000_000 * pricing["output"]
            + usage.get("cache_read", 0) / 1_000_000 * pricing["cache_read"]
            + usage.get("cache_write", 0) / 1_000_000 * pricing["cache_write"]
        )

    def compute_actual_cost(self, usage_breakdown: dict[str, dict[str, int]]) -> dict[str, float]:
        """Compute real USD from observed token counts.

        usage_breakdown is keyed by stage: 'per_slide', 'storyline', 'visual'.
        Returns dict with per-stage USD and a total.
        """
        per_slide_usd = self._stage_cost(usage_breakdown.get("per_slide", {}), self.pricing_per_slide)
        storyline_usd = self._stage_cost(usage_breakdown.get("storyline", {}), self.pricing_storyline)
        visual_usd = self._stage_cost(usage_breakdown.get("visual", {}), self.pricing_visual)
        return {
            "provider": self.name,
            "per_slide_usd": per_slide_usd,
            "storyline_usd": storyline_usd,
            "visual_usd": visual_usd,
            "total_usd": per_slide_usd + storyline_usd + visual_usd,
        }


# ===========================================================================
# Claude provider
# ===========================================================================

class ClaudeProvider(Provider):
    name = "claude"
    per_slide_model = "claude-sonnet-4-6"
    storyline_model = "claude-opus-4-7"
    visual_model = "claude-opus-4-7"

    # USD per 1M tokens
    pricing_per_slide = {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75}
    pricing_storyline = {"input": 5.00, "output": 25.00, "cache_read": 0.50, "cache_write": 6.25}
    pricing_visual    = {"input": 5.00, "output": 25.00, "cache_read": 0.50, "cache_write": 6.25}

    def __init__(self, api_key: str | None = None):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def analyze_slide(self, slide, file_name):
        user_msg = _build_slide_user_message(slide, file_name)
        response = self.client.messages.create(
            model=self.per_slide_model,
            max_tokens=2000,
            system=[
                {"type": "text", "text": PER_SLIDE_SYSTEM, "cache_control": {"type": "ephemeral"}}
            ],
            output_config={"format": {"type": "json_schema", "schema": PER_SLIDE_SCHEMA}},
            messages=[{"role": "user", "content": user_msg}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "{}")
        parsed = json.loads(text)
        parsed["slide_number"] = slide["slide_number"]
        parsed["_usage"] = _normalize_usage_anthropic(response.usage)
        return parsed

    def analyze_storyline(self, file_name, deck, findings):
        digest = _build_storyline_digest(file_name, deck, findings)
        response = self.client.messages.create(
            model=self.storyline_model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={
                "effort": "high",
                "format": {"type": "json_schema", "schema": STORYLINE_SCHEMA},
            },
            system=[
                {"type": "text", "text": STORYLINE_SYSTEM, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": digest}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "{}")
        parsed = json.loads(text)
        parsed["_usage"] = _normalize_usage_anthropic(response.usage)
        return parsed

    def analyze_visual(self, slide_number, images, slide_title, body_text):
        # Claude vision only accepts these formats — filter unsupported
        # embedded image types (emf, wmf, tiff, bmp, svg, etc.) which would
        # cause a 400 invalid_request_error from the API.
        SUPPORTED = {"jpeg", "jpg", "png", "gif", "webp"}
        filtered = [(b, e) for b, e in images if e.lower() in SUPPORTED]

        if not filtered:
            return {
                "slide_number": slide_number,
                "visual_quality": {
                    "ok": True,
                    "notes": (
                        f"Slide tiene {len(images)} imagen(es) en formato no "
                        f"soportado por la API de visión (ej: emf/wmf/tiff). "
                        f"No se pudo analizar."
                    ),
                    "suggestion": None,
                },
                "chart_readability": {
                    "present": False, "ok": True,
                    "notes": "Formato no soportado.", "suggestion": None,
                },
                "design_issues": [],
                "_usage": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
            }

        skipped_count = len(images) - len(filtered)
        skipped_note = (
            f" (Se saltaron {skipped_count} imagen(es) en formato no soportado.)"
            if skipped_count else ""
        )

        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"Slide número: {slide_number}\n"
                    f"Título: {slide_title or '(sin título)'}\n"
                    f"Cuerpo de texto:\n{body_text or '(vacío)'}\n\n"
                    f"A continuación van {len(filtered)} imagen(es) embebida(s)."
                    f"{skipped_note}"
                ),
            }
        ]
        for img_bytes, ext in filtered:
            media_type = (
                "image/jpeg" if ext.lower() in ("jpg", "jpeg") else f"image/{ext.lower()}"
            )
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.b64encode(img_bytes).decode("ascii"),
                    },
                }
            )
        response = self.client.messages.create(
            model=self.visual_model,
            max_tokens=3000,
            thinking={"type": "adaptive"},
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": VISUAL_SCHEMA},
            },
            system=[
                {"type": "text", "text": VISUAL_SYSTEM, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": content}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "{}")
        parsed = json.loads(text)
        parsed["slide_number"] = slide_number
        parsed["_usage"] = _normalize_usage_anthropic(response.usage)
        return parsed


# ===========================================================================
# OpenAI provider
# ===========================================================================

class OpenAIProvider(Provider):
    name = "openai"
    per_slide_model = "gpt-4o"
    storyline_model = "gpt-4o"
    visual_model = "gpt-4o"

    # USD per 1M tokens. OpenAI's cached input is ~50% of standard input.
    # cache_write is 0 since OpenAI doesn't separately bill for cache writes.
    pricing_per_slide = {"input": 2.50, "output": 10.00, "cache_read": 1.25, "cache_write": 2.50}
    pricing_storyline = {"input": 2.50, "output": 10.00, "cache_read": 1.25, "cache_write": 2.50}
    pricing_visual    = {"input": 2.50, "output": 10.00, "cache_read": 1.25, "cache_write": 2.50}

    def __init__(self, api_key: str | None = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def _structured_call(
        self,
        *,
        model: str,
        system: str,
        user_content: Any,  # str or list of content blocks
        schema: dict[str, Any],
        schema_name: str,
        max_tokens: int = 2000,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
            max_completion_tokens=max_tokens,
        )
        text = response.choices[0].message.content or "{}"
        return json.loads(text), _normalize_usage_openai(response.usage)

    def analyze_slide(self, slide, file_name):
        user_msg = _build_slide_user_message(slide, file_name)
        parsed, usage = self._structured_call(
            model=self.per_slide_model,
            system=PER_SLIDE_SYSTEM,
            user_content=user_msg,
            schema=PER_SLIDE_SCHEMA,
            schema_name="PerSlideQA",
            max_tokens=2000,
        )
        parsed["slide_number"] = slide["slide_number"]
        parsed["_usage"] = usage
        return parsed

    def analyze_storyline(self, file_name, deck, findings):
        digest = _build_storyline_digest(file_name, deck, findings)
        parsed, usage = self._structured_call(
            model=self.storyline_model,
            system=STORYLINE_SYSTEM,
            user_content=digest,
            schema=STORYLINE_SCHEMA,
            schema_name="StorylineQA",
            max_tokens=8000,
        )
        parsed["_usage"] = usage
        return parsed

    def analyze_visual(self, slide_number, images, slide_title, body_text):
        # GPT-4o vision only accepts these formats.
        SUPPORTED = {"jpeg", "jpg", "png", "gif", "webp"}
        filtered = [(b, e) for b, e in images if e.lower() in SUPPORTED]

        if not filtered:
            return {
                "slide_number": slide_number,
                "visual_quality": {
                    "ok": True,
                    "notes": (
                        f"Slide tiene {len(images)} imagen(es) en formato no "
                        f"soportado por la API de visión (ej: emf/wmf/tiff). "
                        f"No se pudo analizar."
                    ),
                    "suggestion": None,
                },
                "chart_readability": {
                    "present": False, "ok": True,
                    "notes": "Formato no soportado.", "suggestion": None,
                },
                "design_issues": [],
                "_usage": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
            }

        skipped_count = len(images) - len(filtered)
        skipped_note = (
            f" (Se saltaron {skipped_count} imagen(es) en formato no soportado.)"
            if skipped_count else ""
        )

        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"Slide número: {slide_number}\n"
                    f"Título: {slide_title or '(sin título)'}\n"
                    f"Cuerpo de texto:\n{body_text or '(vacío)'}\n\n"
                    f"A continuación van {len(filtered)} imagen(es) embebida(s)."
                    f"{skipped_note}"
                ),
            }
        ]
        for img_bytes, ext in filtered:
            media_type = "jpeg" if ext.lower() in ("jpg", "jpeg") else ext.lower()
            b64 = base64.b64encode(img_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{media_type};base64,{b64}"},
                }
            )
        parsed, usage = self._structured_call(
            model=self.visual_model,
            system=VISUAL_SYSTEM,
            user_content=content,
            schema=VISUAL_SCHEMA,
            schema_name="VisualQA",
            max_tokens=3000,
        )
        parsed["slide_number"] = slide_number
        parsed["_usage"] = usage
        return parsed


# ===========================================================================
# Factory + registry
# ===========================================================================

PROVIDERS: dict[str, type[Provider]] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def make_provider(name: str, api_key: str | None = None) -> Provider:
    """Instantiate a provider by name."""
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name!r}. Valid: {list(PROVIDERS)}")
    return cls(api_key=api_key)


def provider_pricing_table() -> dict[str, dict[str, Any]]:
    """Static pricing table for use by the UI to show comparisons without instantiating."""
    table = {}
    for name, cls in PROVIDERS.items():
        table[name] = {
            "models": {
                "per_slide": cls.per_slide_model,
                "storyline": cls.storyline_model,
                "visual": cls.visual_model,
            },
            "pricing": {
                "per_slide": cls.pricing_per_slide,
                "storyline": cls.pricing_storyline,
                "visual": cls.pricing_visual,
            },
        }
    return table
