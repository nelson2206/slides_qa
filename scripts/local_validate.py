"""End-to-end local validation. NO API calls.

Steps:
1. Build the good and bad fixture decks.
2. Run the extractor.
3. Run the local QA pipeline (deterministic only).
4. Assert that the BAD deck produces the expected red flags and the GOOD deck stays clean.
5. Print a human-readable summary.

Run from the project root:
    python scripts/local_validate.py
or:
    .venv/Scripts/python.exe scripts/local_validate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extractor import extract_deck
from fixtures.synth import BAD_DECK_FILENAME, GOOD_DECK_FILENAME, build_bad_deck, build_good_deck
from qa import run_local_qa


def _consume(gen):
    result = None
    statuses = []
    for kind, payload in gen:
        if kind == "status":
            statuses.append(payload)
        elif kind == "result":
            result = payload
        elif kind == "error":
            raise RuntimeError(f"Pipeline error: {payload}")
    return result, statuses


def _print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def validate_bad(workdir: Path) -> list[str]:
    failures: list[str] = []
    path = build_bad_deck(workdir / BAD_DECK_FILENAME)
    deck = extract_deck(path)
    result, statuses = _consume(run_local_qa(BAD_DECK_FILENAME, deck))

    _print_section(f"BAD deck — {BAD_DECK_FILENAME}")
    for s in statuses:
        print(f"  [status] {s}")

    overview = result["deck_overview"]
    print(f"\n  filename_subtitle_alignment: {overview['filename_subtitle_alignment']}")
    print(f"  footer_alignment.ok:         {overview['footer_alignment_detail']['ok']}")
    print(f"  footer_text_consistency.ok:  {overview['footer_text_consistency_detail']['ok']}")

    # Expectations
    if overview["filename_alignment_detail"]["cover_aligned"]:
        failures.append("BAD deck cover should NOT match filename keywords")

    if overview["footer_alignment_detail"]["ok"]:
        failures.append("BAD deck footers should be flagged as misaligned")

    if overview["footer_text_consistency_detail"]["ok"]:
        failures.append("BAD deck footers should be flagged as inconsistent")

    print("\n  Per-slide:")
    for slide in result["slides"]:
        n = slide["slide_number"]
        tl = slide["text_length"]
        ft = slide["footer"]
        print(
            f"    Slide {n}: score={slide['score']}, text_length.ok={tl['ok']}, "
            f"footer.present={ft['present']}, footer.aligned={ft['aligned']}"
        )

    # Slide 2 should be flagged
    slide_2 = result["slides"][1]
    if slide_2["text_length"]["ok"]:
        failures.append("BAD deck slide 2 should be flagged for long paragraphs")
    if slide_2["score"] >= 10:
        failures.append(f"BAD deck slide 2 score too high: {slide_2['score']}")

    return failures


def validate_good(workdir: Path) -> list[str]:
    failures: list[str] = []
    path = build_good_deck(workdir / GOOD_DECK_FILENAME)
    deck = extract_deck(path)
    result, statuses = _consume(run_local_qa(GOOD_DECK_FILENAME, deck))

    _print_section(f"GOOD deck — {GOOD_DECK_FILENAME}")
    for s in statuses:
        print(f"  [status] {s}")

    overview = result["deck_overview"]
    print(f"\n  filename_subtitle_alignment: {overview['filename_subtitle_alignment']}")
    print(f"  footer_alignment.ok:         {overview['footer_alignment_detail']['ok']}")
    print(f"  footer_text_consistency.ok:  {overview['footer_text_consistency_detail']['ok']}")
    print(f"  footer_matches_deck_title:   {overview['footer_matches_deck_title_detail']['ok']}")

    if not overview["filename_alignment_detail"]["cover_aligned"]:
        failures.append("GOOD deck cover SHOULD match filename keywords")

    if not overview["footer_alignment_detail"]["ok"]:
        failures.append("GOOD deck footers should be aligned")

    if not overview["footer_text_consistency_detail"]["ok"]:
        failures.append("GOOD deck footers should be text-consistent")

    if not overview["footer_matches_deck_title_detail"]["ok"]:
        failures.append("GOOD deck footers should match the deck title from cover")

    print("\n  Per-slide:")
    for slide in result["slides"]:
        n = slide["slide_number"]
        tl = slide["text_length"]
        ft = slide["footer"]
        print(
            f"    Slide {n}: score={slide['score']}, text_length.ok={tl['ok']}, "
            f"footer.present={ft['present']}, footer.aligned={ft['aligned']}"
        )

    for slide in result["slides"]:
        if not slide["text_length"]["ok"]:
            failures.append(
                f"GOOD deck slide {slide['slide_number']} should NOT be flagged for long paragraphs"
            )

    return failures


def main() -> int:
    workdir = Path(__file__).resolve().parent.parent / "build" / "fixtures"
    workdir.mkdir(parents=True, exist_ok=True)

    print("PPT QA Agent — Local Validation (no API)")
    print("=" * 60)

    all_failures: list[str] = []
    all_failures.extend(validate_bad(workdir))
    all_failures.extend(validate_good(workdir))

    _print_section("Resumen")
    if all_failures:
        print(f"\n  [FAIL] {len(all_failures)} expectativa(s) no cumplida(s):")
        for f in all_failures:
            print(f"     - {f}")
        return 1

    print("\n  [OK] Validacion local OK -- todos los checks deterministicos se comportan como esperamos.")
    print(f"\n  Fixtures generadas en: {workdir}")
    return 0


if __name__ == "__main__":
    # Force UTF-8 stdout on Windows so accented chars in fixture content don't crash.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
    sys.exit(main())
