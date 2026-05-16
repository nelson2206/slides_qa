"""Shared fixtures. All deck generation is local — no API calls."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the project root importable when running pytest from any directory.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fixtures.synth import (
    BAD_DECK_FILENAME,
    GOOD_DECK_FILENAME,
    IMAGE_DECK_FILENAME,
    build_bad_deck,
    build_deck_with_image,
    build_good_deck,
)


@pytest.fixture
def bad_deck_path(tmp_path: Path) -> Path:
    return build_bad_deck(tmp_path / BAD_DECK_FILENAME)


@pytest.fixture
def good_deck_path(tmp_path: Path) -> Path:
    return build_good_deck(tmp_path / GOOD_DECK_FILENAME)


@pytest.fixture
def image_deck_path(tmp_path: Path) -> Path:
    return build_deck_with_image(tmp_path / IMAGE_DECK_FILENAME)
