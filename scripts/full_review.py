"""Run the FULL QA pipeline (deterministic + Sonnet per-slide + Opus storyline).

This costs tokens. Estimates cost before running and asks for confirmation
unless --yes is passed.

Usage:
    python scripts/full_review.py <pptx-path>
    python scripts/full_review.py <pptx-path> --yes
    python scripts/full_review.py <pptx-path> --max-slides 10   # smoke test on first N
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extractor import extract_deck
from keyloader import load_api_key
from pricing import estimate_cost
from qa import run_full_qa


def _bool(v, na="?"):
    if v is None:
        return na
    return "OK" if v else "REVISAR"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pptx_path")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="No pedir confirmación previa")
    parser.add_argument("--max-slides", type=int, default=None,
                        help="Solo procesar los primeros N slides (smoke test)")
    parser.add_argument("--out-json", default=None,
                        help="Path para escribir el reporte completo en JSON")
    parser.add_argument("--out-md", default=None,
                        help="Path para escribir un reporte markdown")
    args = parser.parse_args()

    path = Path(args.pptx_path)
    if not path.exists():
        print(f"No existe: {path}")
        return 1

    api_key, source = load_api_key()
    if not api_key:
        print("ERROR: no se pudo cargar ANTHROPIC_API_KEY.")
        print("Drop una de:")
        print(f"  - {ROOT}\\.env con la línea: ANTHROPIC_API_KEY=sk-ant-...")
        print(f"  - {ROOT}\\api_key.txt con la key cruda (una línea)")
        print(f"  - O setear la variable de entorno antes de correr.")
        return 2

    print(f"API key cargada de: {source}")
    print(f"Archivo: {path.name}")
    print(f"Tamaño:  {path.stat().st_size / 1024:.1f} KB")

    print("Extrayendo deck...")
    deck = extract_deck(path)
    full_count = deck["slide_count"]
    print(f"  slides totales: {full_count}")

    if args.max_slides and args.max_slides < full_count:
        deck["slides"] = deck["slides"][: args.max_slides]
        deck["slide_count"] = len(deck["slides"])
        print(f"  smoke test: procesando solo los primeros {deck['slide_count']}")

    est = estimate_cost(deck["slide_count"])
    print()
    print("Costo estimado (orden de magnitud):")
    print(f"  Sonnet por slide ({deck['slide_count']} slides):  ~${est['sonnet_usd']:.3f}")
    print(f"  Opus storyline (1 call):              ~${est['opus_usd']:.3f}")
    print(f"  TOTAL:                                ~${est['total_usd']:.3f}")
    print()

    if not args.yes:
        ans = input("Continuar y gastar tokens? [y/N]: ").strip().lower()
        if ans not in ("y", "yes", "s", "si", "sí"):
            print("Cancelado.")
            return 0

    print("\nCorriendo modo full...")
    result = None
    for kind, payload in run_full_qa(path.name, deck, api_key=api_key):
        if kind == "status":
            print(f"  [status] {payload}")
        elif kind == "error":
            print(f"  [error]  {payload}")
        elif kind == "result":
            result = payload

    if result is None:
        return 3

    overview = result["deck_overview"]
    print()
    print("=" * 70)
    print("VISTA GLOBAL (modo full)")
    print("=" * 70)
    print(f"Storyline coherente:          {_bool(overview['storyline_coherent'])}")
    print(f"Storyline notes:")
    for line in overview["storyline_notes"].split(". "):
        if line.strip():
            print(f"  {line.strip()}")
    print(f"\nFilename <-> subtítulos:      {overview['filename_subtitle_alignment']}")

    if overview.get("cross_slide_issues"):
        print(f"\nIssues cross-slide ({len(overview['cross_slide_issues'])}):")
        for issue in overview["cross_slide_issues"]:
            slides = ", ".join(str(s) for s in issue["slide_numbers"])
            print(f"  - Slides {slides}: {issue['issue']}")

    print(f"\nUso de tokens:")
    u = result["usage"]
    print(f"  Sonnet (per-slide x {deck['slide_count']}):")
    print(f"    input:       {u['sonnet_per_slide']['input']:>8,}")
    print(f"    cache write: {u['sonnet_per_slide']['cache_write']:>8,}")
    print(f"    cache read:  {u['sonnet_per_slide']['cache_read']:>8,}")
    print(f"    output:      {u['sonnet_per_slide']['output']:>8,}")
    print(f"  Opus (storyline):")
    print(f"    input:       {u['opus_storyline'].get('input', 0):>8,}")
    print(f"    cache write: {u['opus_storyline'].get('cache_write', 0):>8,}")
    print(f"    cache read:  {u['opus_storyline'].get('cache_read', 0):>8,}")
    print(f"    output:      {u['opus_storyline'].get('output', 0):>8,}")

    print()
    print("=" * 70)
    print("POR SLIDE")
    print("=" * 70)
    for slide in result["slides"]:
        n = slide["slide_number"]
        role = slide.get("role", "?")
        score = slide["score"]
        at = slide["action_title"]
        sw = slide["so_what"]
        cc = slide["cause_consequence"]
        flag = "* " if score is not None and score < 7 else "  "
        title_disp = (at["current_title"][:70] + "...") if len(at["current_title"]) > 70 else at["current_title"]
        print(f"{flag}Slide {n:>2}  role={role:18}  score={score}/10")
        print(f"   título: {title_disp!r}")
        print(f"   action_title: {_bool(at['is_action_title'])} — {at['notes']}")
        if at.get("suggestion"):
            print(f"     => sugerencia: {at['suggestion']}")
        print(f"   so_what:      {_bool(sw['present'])} — {sw['notes']}")
        if sw.get("suggestion"):
            print(f"     => sugerencia: {sw['suggestion']}")
        print(f"   causa→cons:   {_bool(cc['ok'])} — {cc['notes']}")
        print()

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON completo escrito en: {args.out_json}")

    if args.out_md:
        _write_md(result, path.name, Path(args.out_md))
        print(f"Reporte markdown escrito en: {args.out_md}")

    return 0


def _write_md(result: dict, file_name: str, out: Path) -> None:
    overview = result["deck_overview"]
    lines: list[str] = []
    lines.append(f"# Reporte QA Full — {file_name}\n")
    lines.append(f"## Vista global\n")
    lines.append(f"- **Storyline coherente:** {overview.get('storyline_coherent')}")
    lines.append(f"- **Storyline:** {overview.get('storyline_notes')}")
    lines.append(f"- **Filename ↔ subtítulos:** {overview.get('filename_subtitle_alignment')}\n")
    if overview.get("cross_slide_issues"):
        lines.append("### Issues cross-slide\n")
        for issue in overview["cross_slide_issues"]:
            slides = ", ".join(str(s) for s in issue["slide_numbers"])
            lines.append(f"- Slides {slides}: {issue['issue']}")
        lines.append("")
    lines.append("## Slides\n")
    for slide in result["slides"]:
        score_str = f"{slide['score']}/10" if slide["score"] is not None else "—"
        lines.append(f"### Slide {slide['slide_number']} — {score_str} ({slide.get('role','?')})")
        lines.append(f"_{slide['summary']}_\n")
        at = slide["action_title"]
        lines.append(f"**Title actual:** `{at['current_title']}`")
        lines.append(f"- **Action title** ({'OK' if at['is_action_title'] else 'revisar'}): {at['notes']}")
        if at.get("suggestion"):
            lines.append(f"  - Sugerencia: {at['suggestion']}")
        sw = slide["so_what"]
        lines.append(f"- **So-what** ({'OK' if sw['present'] else 'revisar'}): {sw['notes']}")
        if sw.get("suggestion"):
            lines.append(f"  - Sugerencia: {sw['suggestion']}")
        cc = slide["cause_consequence"]
        lines.append(f"- **Causa→cons** ({'OK' if cc['ok'] else 'revisar'}): {cc['notes']}")
        tl = slide["text_length"]
        lines.append(f"- **Largo de párrafos** ({'OK' if tl['ok'] else 'revisar'}): {tl.get('notes','')}")
        for p in tl.get("long_paragraphs", []):
            lines.append(f"  - > {p}")
        if tl.get("suggestion"):
            lines.append(f"  - Sugerencia: {tl['suggestion']}")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
    sys.exit(main())
