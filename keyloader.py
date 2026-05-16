"""Load API keys from common locations.

Supports both ANTHROPIC_API_KEY and OPENAI_API_KEY. Lookup order:
1. Environment variable (ANTHROPIC_API_KEY / OPENAI_API_KEY)
2. .env file (KEY=VALUE format)
3. api_key.txt (raw key, Anthropic-only — legacy)
4. .anthropic_key / .openai_key (raw key, single line)

All file-based options are in .gitignore.
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

KEY_TO_ENV = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

KEY_TO_RAW_FILES = {
    "claude": ("api_key.txt", ".anthropic_key"),
    "openai": (".openai_key", "openai_key.txt"),
}


def _parse_env_file(env_file: Path, want_keys: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    if not env_file.exists():
        return out
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k in want_keys:
            v = v.strip().strip('"').strip("'")
            if v:
                out[k] = v
    return out


def load_api_key(provider: str = "claude") -> tuple[str | None, str]:
    """Load the API key for `provider` ('claude' or 'openai').

    Returns (key, source_description). If not found, key is None.
    """
    env_var = KEY_TO_ENV.get(provider)
    if not env_var:
        return None, f"provider desconocido: {provider!r}"

    if env_val := os.environ.get(env_var):
        return env_val.strip(), f"{env_var} env var"

    env_file = PROJECT_ROOT / ".env"
    parsed = _parse_env_file(env_file, list(KEY_TO_ENV.values()))
    if env_var in parsed:
        return parsed[env_var], f".env ({env_file.name})"

    for fname in KEY_TO_RAW_FILES.get(provider, ()):
        f = PROJECT_ROOT / fname
        if f.exists():
            content = f.read_text(encoding="utf-8").strip()
            if content:
                return content, fname

    return None, f"no se encontró {env_var} en env, .env, ni archivos crudos"


def load_all_keys() -> dict[str, tuple[str | None, str]]:
    """Convenience: return {provider: (key, source)} for all providers."""
    return {p: load_api_key(p) for p in KEY_TO_ENV}


def mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 12:
        return "***"
    return f"{key[:7]}...{key[-4:]}"
