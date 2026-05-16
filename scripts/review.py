"""Run the local (no-API) QA pipeline on a real .pptx and print a readable report.

Usage:
    python scripts/review.py "<path-to-pptx>"
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extractor import extract_deck
from qa import run_local_qa


def _consume(gen):
    result = None
    for kind, payload in gen:
        if kind == "result":
            result = payload
        elif kind == "status":
            print(f"  [status] {payload}")
        elif kind == "error":
            print(f"  [error]  {payload}")
    return result


def _bool(v, na="?"):
    if v is None:
        return na
    return "OK" if v else "REVISAR"


def main(pptx_path: str) -> int:
    path = Path(pptx_path)
    if not path.exists():
        print(f"No existe el archivo: {path}")
        return 1

    print(f"\nArchivo: {path.name}")
    print(f"Tamaño:  {path.stat().st_size / 1024:.1f} KB")
    print("-" * 70)

    print("Extrayendo deck...")
    deck = extract_deck(path)
    print(
        f"  slides: {deck['slide_count']}   "
        f"tamaño slide: {deck['slide_width_in']}\" x {deck['slide_height_in']}\""
    )
    print()

    print("Corriendo QA (modo local, sin API)...")
    result = _consume(run_local_qa(path.name, deck))
    if result is None:
        return 2

    overview = result["deck_overview"]
    print()
    print("=" * 70)
    print("VISTA GLOBAL")
    print("=" * 70)
    print(f"Modo:                         {result['mode']}")
    print(f"Storyline coherente:          {_bool(overview['storyline_coherent'], na='requiere API')}")
    print(f"Storyline notes:              {overview['storyline_notes']}")
    print(f"Filename <-> títulos:         {overview['filename_subtitle_alignment']}")

    fa = overview["filename_alignment_detail"]
    print(f"  Filename keywords:          {fa.get('filename_keywords', [])}")
    print(f"  Slides con overlap:         {[m['slide_number'] for m in fa.get('matches', [])]}")
    print(f"  Portada alineada:           {fa.get('cover_aligned')}")

    fa_geom = overview["footer_alignment_detail"]
    print(f"\nPie de página (geometría):")
    print(f"  Aplicable:                  {fa_geom.get('applicable')}")
    print(f"  Alineación OK:              {fa_geom.get('ok')}")
    print(f"  Notes:                      {fa_geom.get('notes')}")
    if fa_geom.get("findings"):
        for f in fa_geom["findings"]:
            print(
                f"    - Slide {f['slide_number']}: top={f['top_in']}in, "
                f"left={f.get('left_in')}in, height={f['height_in']}in, text={f['text']!r}"
            )

    ftc = overview.get("footer_text_consistency_detail", {})
    print(f"\nPie de página (texto consistente):")
    print(f"  Aplicable:                  {ftc.get('applicable')}")
    print(f"  OK:                         {ftc.get('ok')}")
    print(f"  Notes:                      {ftc.get('notes', '-')}")
    if ftc.get("variations"):
        for v in ftc["variations"]:
            print(f"    - {v['count']}x: {v['text']!r}")

    fmt = overview.get("footer_matches_deck_title_detail", {})
    print(f"\nPie de página (repite título del deck):")
    print(f"  Aplicable:                  {fmt.get('applicable')}")
    print(f"  OK:                         {fmt.get('ok')}")
    print(f"  Notes:                      {fmt.get('notes', '-')}")
    if fmt.get("cover_title"):
        print(f"  Título de portada:          {fmt['cover_title']!r}")
    if fmt.get("matching_slides"):
        print(f"  Slides que matchean:        {fmt['matching_slides']}")

    caps = overview.get("footer_caps_detail", {})
    print(f"\nPie de página (caps consistency):")
    print(f"  Aplicable:                  {caps.get('applicable')}")
    print(f"  Consistente:                {caps.get('ok')}")
    print(f"  Notes:                      {caps.get('notes', '-')}")
    if caps.get("outliers"):
        print("  Outliers (estilo distinto al dominante):")
        for o in caps["outliers"]:
            print(f"    - Slide {o['slide_number']}: style={o['style']!r}, text={o['text']!r}")

    sub = overview.get("subtitle_filename_alignment_detail", {})
    print(f"\nSubtítulos <-> filename:")
    print(f"  Aplicable:                  {sub.get('applicable')}")
    print(f"  OK:                         {sub.get('ok')}")
    print(f"  Notes:                      {sub.get('notes', '-')}")
    if sub.get("subtitles"):
        for s in sub["subtitles"]:
            print(f"    - Slide {s['slide_number']}: {s['text']!r}")
    if sub.get("matches"):
        print("  Matches con filename:")
        for m in sub["matches"]:
            print(f"    - Slide {m['slide_number']}: shared={m['shared']}")

    tf = overview.get("title_format_consistency_detail", {})
    print(f"\nConsistencia de formato de títulos:")
    print(f"  Aplicable:                  {tf.get('applicable')}")
    print(f"  OK:                         {tf.get('ok')}")
    print(f"  Counts:                     {tf.get('counts', {})}")
    print(f"  Notes:                      {tf.get('notes', '-')}")

    dup = overview.get("duplicate_titles_detail", {})
    print(f"\nTítulos duplicados:")
    print(f"  OK (todos únicos):          {dup.get('ok')}")
    if dup.get("duplicates"):
        for d in dup["duplicates"]:
            title_disp = (d["title"][:60] + "...") if len(d["title"]) > 60 else d["title"]
            print(f"    - {title_disp!r} en slides {d['slide_numbers']}")

    print()
    print("=" * 70)
    print("POR SLIDE")
    print("=" * 70)
    flagged: list[int] = []
    role_counts: dict[str, int] = {}
    for slide in result["slides"]:
        n = slide["slide_number"]
        score = slide["score"]
        tl = slide["text_length"]
        footer = slide["footer"]
        role = slide.get("role", "?")
        role_counts[role] = role_counts.get(role, 0) + 1
        title = slide["action_title"]["current_title"]
        title_disp = (title[:60] + "...") if len(title) > 60 else title

        flag = "  "
        if score is not None and score < 10:
            flag = "* "
            flagged.append(n)

        print(f"{flag}Slide {n:>2}  role={role:18}  score={score}/10  title={title_disp!r}")
        print(f"   length.ok={_bool(tl['ok'])}  ({tl['notes']})")
        for lp in tl.get("long_paragraphs", []):
            print(f"     - {lp}")
        if tl.get("suggestion"):
            print(f"     sugerencia: {tl['suggestion']}")

        if footer["present"]:
            print(f"   pie de pag: presente, aligned={_bool(footer['aligned'])}, text={footer.get('current_footer')!r}")
        else:
            print(f"   pie de pag: ausente")
        print()

    print("=" * 70)
    print("RESUMEN")
    print(f"  Slides por rol:           {role_counts}")
    print(f"  Slides con flags:         {len(flagged)} -> {flagged}")
    content_no_title = [s["slide_number"] for s in result["slides"] if s.get("role") == "content_no_title"]
    if content_no_title:
        print(f"  Contenido SIN título:     {content_no_title}")
    print(f"\n  (Los checks semánticos -- action title, so-what, storyline --")
    print(f"   requieren modo full con API; este reporte es solo local.)")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
    if len(sys.argv) < 2:
        print("Uso: python scripts/review.py <path-to-pptx>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
