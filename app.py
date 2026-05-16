"""PPT QA Agent — Streamlit web app (Recreo-inspired design)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

import styles
from extractor import extract_deck, extract_images
from keyloader import load_all_keys, mask
from pricing import compare_providers, estimate_cost
from providers import PROVIDERS, provider_pricing_table
from qa import (
    DEFAULT_SKIP_ROLES,
    SEVERITY_EMOJI,
    SEVERITY_LABELS,
    SEVERITY_ORDER,
    run_full_qa,
    run_local_qa,
    severity_for,
)
from renderer import (
    cache_key_for,
    is_libreoffice_available,
    is_powerpoint_available,
    render_schematic_for_deck,
    render_via_libreoffice,
    render_via_powerpoint,
)


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PPT QA Agent",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)
styles.inject()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

styles.eyebrow("PPT QA Agent")
st.markdown("# Calidad por slide, sin discusión")
st.markdown(
    '<p style="color: var(--text-muted); font-size: 0.95rem; max-width: 62ch; '
    'margin: -0.3rem 0 1rem 0; line-height: 1.5;">'
    "Action titles, so-what, storyline, longitud de párrafos, pie de página, "
    "consistencia editorial y análisis visual. Modo local sin API · modo completo "
    "con Claude o GPT-4o."
    '</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar — global configuration
# ---------------------------------------------------------------------------

PROVIDER_LABELS = {
    "claude": "Claude — Sonnet 4.6 + Opus 4.7",
    "openai": "OpenAI — GPT-4o",
}

with st.sidebar:
    styles.section_label("Modo")
    mode = st.radio(
        "Modo",
        options=["local", "full"],
        format_func=lambda m: {"local": "Local · sin API", "full": "Completo · con API"}[m],
        label_visibility="collapsed",
    )

    selected_provider = "claude"
    api_key = None
    api_key_source = None

    if mode == "full":
        st.markdown("")
        styles.section_label("Provider")
        selected_provider = st.radio(
            "Provider",
            options=list(PROVIDERS.keys()),
            format_func=lambda p: PROVIDER_LABELS.get(p, p),
            label_visibility="collapsed",
        )

        with st.expander("Comparar pricing"):
            table = provider_pricing_table()
            for p, info in table.items():
                st.markdown(f"**{PROVIDER_LABELS.get(p, p)}**")
                pp = info["pricing"]["per_slide"]
                ps = info["pricing"]["storyline"]
                st.caption(
                    f"Per slide · `{info['models']['per_slide']}` "
                    f"(${pp['input']:.2f} / ${pp['output']:.2f} por 1M)  \n"
                    f"Storyline · `{info['models']['storyline']}` "
                    f"(${ps['input']:.2f} / ${ps['output']:.2f} por 1M)"
                )

        st.markdown("")
        styles.section_label("API key")
        all_keys = load_all_keys()
        api_key, source = all_keys.get(selected_provider, (None, "no provider"))
        if api_key:
            api_key_source = source
            st.markdown(
                styles.pill(f"Cargada · {mask(api_key)}", "ok"),
                unsafe_allow_html=True,
            )
            st.caption(f"De: `{source}`")
        else:
            st.markdown(styles.pill("Sin key", "crit"), unsafe_allow_html=True)
            st.caption(source)
            with st.expander("Configurar"):
                env_var = "ANTHROPIC_API_KEY" if selected_provider == "claude" else "OPENAI_API_KEY"
                st.markdown(
                    f"Creá uno de estos archivos en el root:  \n"
                    f"`.env` → `{env_var}=...`  \n"
                    f"O setear la env var `{env_var}` antes de lanzar."
                )
            manual = st.text_input(
                "O pegala acá",
                type="password",
                key=f"manual_{selected_provider}",
                placeholder="sk-...",
            )
            if manual:
                api_key = manual.strip()
                api_key_source = "input manual"

        # Other provider availability
        other = "openai" if selected_provider == "claude" else "claude"
        other_key, other_src = all_keys.get(other, (None, ""))
        if other_key:
            st.caption(f"{PROVIDER_LABELS[other]} también disponible.")

    st.markdown("---")
    styles.section_label("Miniaturas de slides")
    pp_avail, pp_source = is_powerpoint_available()
    lo_avail, lo_source = is_libreoffice_available()

    available_modes = ["off", "schematic"]
    if lo_avail:
        available_modes.append("libreoffice")
    if pp_avail:
        available_modes.append("powerpoint")

    mode_labels = {
        "off": "Off · solo número",
        "schematic": "Schematic · rápido, deployable",
        "libreoffice": "LibreOffice · fiel, deployable",
        "powerpoint": "PowerPoint · fiel, solo local Windows",
    }

    thumb_mode = st.radio(
        "Renderizado",
        options=available_modes,
        format_func=lambda m: mode_labels.get(m, m),
        label_visibility="collapsed",
        help=(
            "**Schematic**: bounding boxes con Pillow, instantáneo, sin deps.\n\n"
            "**LibreOffice**: render fiel (PDF → PNG). Requiere LibreOffice + poppler. "
            "Es el backend para deployment en Linux/Cloud.\n\n"
            "**PowerPoint**: COM via pywin32. Solo corre en Windows con Office instalado. "
            "**No funciona en servidores/cloud.**"
        ),
    )

    # Status of each backend
    with st.expander("Estado de backends de rendering"):
        st.markdown(f"- **Schematic** (Pillow): ✅ disponible")
        if lo_avail:
            st.markdown(f"- **LibreOffice**: ✅ {lo_source}")
        else:
            st.markdown(f"- **LibreOffice**: ❌ {lo_source}")
        if pp_avail:
            st.markdown(f"- **PowerPoint COM**: ✅ {pp_source}")
        else:
            st.markdown(f"- **PowerPoint COM**: ❌ {pp_source}")
        st.caption(
            "Para producción (compartir el app web a otros): usá **schematic** "
            "siempre, o **LibreOffice** si querés thumbnails fieles (instalalo "
            "en el servidor)."
        )

    st.markdown("---")
    styles.section_label("Checks en este modo")
    if mode == "local":
        st.markdown(
            "Largo de párrafos · pie de página (geometría, texto consistente, "
            "repite título del deck, caps) · slide role · "
            "filename ↔ títulos / subtítulos · formato de títulos · duplicados."
        )
    else:
        st.markdown(
            "Todo lo local **+** action title quality · so-what · "
            "causa→consecuencia · storyline cross-slide · visual de charts (opcional)."
        )


# ---------------------------------------------------------------------------
# Upload area
# ---------------------------------------------------------------------------

uploaded = st.file_uploader(
    "Subí tu presentación", type=["pptx"], label_visibility="collapsed"
)

if uploaded is None:
    st.markdown("")
    st.info("Esperando un `.pptx`. El modo local no gasta tokens.")
    st.stop()

with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
    tmp.write(uploaded.getvalue())
    tmp_path = Path(tmp.name)

try:
    with st.spinner("Extrayendo contenido..."):
        deck = extract_deck(tmp_path)
except Exception as e:
    st.error(f"Error al extraer: {e}")
    try:
        tmp_path.unlink()
    except OSError:
        pass
    st.stop()

file_name = uploaded.name
slides_with_visuals = [s for s in deck["slides"] if s.get("has_visuals")]
n_visuals = len(slides_with_visuals)


def _format_size(bytes_n: int) -> str:
    if bytes_n < 1024 * 1024:
        return f"{bytes_n / 1024:.0f} KB"
    return f"{bytes_n / (1024 * 1024):.1f} MB"


# Cached, session-scoped thumbnail loader. Keyed by (file hash, mode).
def _get_thumbnails(
    pptx_path: Path,
    deck: dict,
    mode: str,
) -> dict[int, bytes]:
    """Render or fetch from cache. Returns {} when mode == 'off'."""
    if mode == "off":
        return {}
    key = f"thumbs__{cache_key_for(pptx_path)}__{mode}"
    if key in st.session_state:
        return st.session_state[key]

    thumbs: dict[int, bytes] = {}
    progress = st.progress(0.0, text=f"Renderizando miniaturas ({mode})…")
    try:
        if mode == "schematic":
            thumbs = render_schematic_for_deck(
                deck,
                progress_cb=lambda done, total: progress.progress(done / max(1, total)),
            )
        elif mode == "libreoffice":
            thumbs = render_via_libreoffice(
                pptx_path,
                progress_cb=lambda done, total: progress.progress(
                    done / max(1, total),
                    text=f"Renderizando con LibreOffice · {done}/{total}",
                ),
            )
        elif mode == "powerpoint":
            thumbs = render_via_powerpoint(
                pptx_path,
                progress_cb=lambda done, total: progress.progress(
                    done / max(1, total),
                    text=f"Renderizando con PowerPoint · {done}/{total}",
                ),
            )
    except Exception as e:
        st.warning(f"Renderizado falló ({mode}): {e}. Sigo sin miniaturas.")
        thumbs = {}
    finally:
        progress.empty()

    st.session_state[key] = thumbs
    return thumbs


# Compact deck summary
st.markdown("")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Slides", deck["slide_count"])
c2.metric("Con imágenes", n_visuals)
c3.metric("Tamaño slide", f'{deck["slide_width_in"]:.1f}″ × {deck["slide_height_in"]:.1f}″')
c4.metric("Peso archivo", _format_size(uploaded.size))

with st.expander("Ver contenido extraído"):
    st.json(deck, expanded=False)


# ---------------------------------------------------------------------------
# Pre-run config — options + cost preview
# ---------------------------------------------------------------------------

slides_to_process = deck["slide_count"]
skip_roles: set[str] | None = None
visual_enabled = False
workers = 6
deck_to_run = deck
est = None

if mode == "full":
    st.markdown("")
    st.markdown("---")
    styles.section_label("Opciones de la corrida")
    st.markdown("")

    o1, o2 = st.columns(2)

    with o1:
        analyze_all = st.checkbox(
            "Evaluar todos los slides (sin skip)",
            value=False,
            help=f"Por defecto se saltean {sorted(DEFAULT_SKIP_ROLES)}.",
        )
        skip_roles = set() if analyze_all else set(DEFAULT_SKIP_ROLES)

        workers = st.slider(
            "Workers en paralelo", min_value=1, max_value=12, value=6,
            help="Más workers = más rápido. 6 es seguro para tier 1.",
        )

    with o2:
        smoke_test = st.checkbox("Smoke test (solo primeros N)", value=False)
        if smoke_test:
            slides_to_process = st.slider(
                "N slides", min_value=1, max_value=deck["slide_count"],
                value=min(5, deck["slide_count"]),
            )

        visual_enabled = st.checkbox(
            f"Analizar charts / imágenes ({n_visuals} con imagen)",
            value=False,
            disabled=(n_visuals == 0),
            help="Pasada extra con visión." if n_visuals > 0 else "Sin imágenes embebidas.",
        )

    if smoke_test and slides_to_process < deck["slide_count"]:
        deck_to_run = {
            **deck,
            "slides": deck["slides"][:slides_to_process],
            "slide_count": slides_to_process,
        }

    from checks import classify_slide_role
    will_skip = sum(1 for s in deck_to_run["slides"] if classify_slide_role(s) in (skip_roles or set()))
    will_visual = sum(1 for s in deck_to_run["slides"] if s.get("has_visuals")) if visual_enabled else 0

    est = estimate_cost(
        deck_to_run["slide_count"],
        skipped_count=will_skip,
        visual_slide_count=will_visual,
        provider=selected_provider,
    )

    # Side-by-side cost comparison
    st.markdown("")
    styles.section_label("Costo estimado · orden de magnitud, ±30%")
    comparison = compare_providers(
        deck_to_run["slide_count"],
        skipped_count=will_skip,
        visual_slide_count=will_visual,
    )
    cmp_cols = st.columns(len(comparison))
    for i, (pname, pest) in enumerate(comparison.items()):
        with cmp_cols[i]:
            label = PROVIDER_LABELS[pname]
            is_selected = pname == selected_provider
            if is_selected:
                styles.cost_panel(
                    f"Seleccionado · {label}",
                    f"${pest['total_usd']:.3f}",
                    sub=(
                        f"per slide ${pest['per_slide_usd']:.3f} · "
                        f"storyline ${pest['storyline_usd']:.3f} · "
                        f"visual ${pest['visual_usd']:.3f}"
                    ),
                )
            else:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.markdown(
                        f"<div style='font-size: 1.5rem; font-weight: 800; color: var(--text-primary); "
                        f"letter-spacing: -0.02em;'>${pest['total_usd']:.3f}</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"per slide ${pest['per_slide_usd']:.3f} · "
                        f"storyline ${pest['storyline_usd']:.3f} · "
                        f"visual ${pest['visual_usd']:.3f}"
                    )

    if not api_key:
        st.error(f"Falta API key para {PROVIDER_LABELS[selected_provider]}. Configurala en el sidebar.")


# ---------------------------------------------------------------------------
# Run button
# ---------------------------------------------------------------------------

can_run = (mode == "local") or (mode == "full" and api_key)
if mode == "local":
    run_label = "Correr análisis local"
elif mode == "full" and api_key:
    run_label = (
        f"Correr con {PROVIDER_LABELS[selected_provider]}  ·  "
        f"{deck_to_run['slide_count']} slides  ·  ~${est['total_usd']:.3f}"
    )
else:
    run_label = "Configurá la API key primero"

st.markdown("")
run_button = st.button(run_label, type="primary", use_container_width=True, disabled=not can_run)

if not run_button:
    try:
        tmp_path.unlink()
    except OSError:
        pass
    st.stop()


# ---------------------------------------------------------------------------
# Pipeline run
# ---------------------------------------------------------------------------

images_by_slide: dict | None = None
if mode == "full" and visual_enabled:
    with st.spinner("Extrayendo imágenes..."):
        images_by_slide = extract_images(tmp_path)
        if slides_to_process < deck["slide_count"]:
            images_by_slide = {n: imgs for n, imgs in images_by_slide.items() if n <= slides_to_process}

# Render thumbnails (needs tmp_path for PowerPoint mode)
thumbs: dict[int, bytes] = {}
if thumb_mode != "off":
    thumbs = _get_thumbnails(tmp_path, deck_to_run, thumb_mode)

try:
    tmp_path.unlink()
except OSError:
    pass

runner = (
    run_local_qa(file_name, deck_to_run)
    if mode == "local"
    else run_full_qa(
        file_name, deck_to_run,
        api_key=api_key,
        provider=selected_provider,
        max_workers=workers,
        skip_roles=skip_roles,
        visual_analysis=visual_enabled,
        images_by_slide=images_by_slide or {},
    )
)

# Streaming UI
st.markdown("---")
styles.section_label("Progreso")
status_box = st.empty()
progress_bar = st.empty()
live_table = st.empty()

completed_slides: list[dict] = []
visual_completed: list[dict] = []
result = None
error = None


def _render_live_table():
    if not completed_slides:
        return
    rows = []
    for entry in completed_slides:
        f = entry["finding"]
        title = f.get("action_title", {}).get("current_title", "")
        title_disp = (title[:60] + "…") if len(title) > 60 else title
        is_at = f.get("action_title", {}).get("is_action_title")
        sw = f.get("so_what", {}).get("present")
        sev = f.get("severity") or severity_for(f.get("score"))
        rows.append({
            "": SEVERITY_EMOJI.get(sev, "·"),
            "Slide": entry["slide_number"],
            "Sev.": SEVERITY_LABELS.get(sev, "—"),
            "Score": f"{f.get('score', '?')}/10",
            "Action title": "✓" if is_at else "✗" if is_at is False else "—",
            "So-what": "✓" if sw else "✗" if sw is False else "—",
            "Título": title_disp,
        })
    rows.sort(key=lambda r: r["Slide"])
    live_table.dataframe(rows, use_container_width=True, hide_index=True)


for kind, payload in runner:
    if kind == "status":
        status_box.info(payload)
    elif kind == "slide_done":
        completed_slides.append(payload)
        progress_bar.progress(
            payload["completed"] / max(1, payload["total"]),
            text=f"{payload['completed']} / {payload['total']} slides analizadas",
        )
        _render_live_table()
    elif kind == "visual_done":
        visual_completed.append(payload)
        status_box.info(f"Visión · {payload['completed']} / {payload['total']}")
    elif kind == "error":
        error = payload
        break
    elif kind == "result":
        result = payload

if error:
    status_box.error(f"Error · {error}")
    st.stop()

if result is None:
    status_box.error("No se recibió resultado.")
    st.stop()

status_box.success("Análisis completo.")
progress_bar.empty()
live_table.empty()


# ---------------------------------------------------------------------------
# Result rendering helpers
# ---------------------------------------------------------------------------

def _status_pill(ok, na_label="N/A"):
    if ok is None:
        return styles.pill(na_label, "muted")
    return styles.pill("OK", "ok") if ok else styles.pill("Revisar", "crit")


def _score_pill(score) -> str:
    if score is None:
        return styles.pill("—", "muted")
    if score >= 8:
        return styles.pill(f"{score}/10", "ok")
    if score >= 5:
        return styles.pill(f"{score}/10", "warn")
    return styles.pill(f"{score}/10", "crit")


# Verdict mappings: (pill_text, pill_variant) for each check given a bool/None value.
def _action_title_pill(verdict: bool | None) -> tuple[str, str]:
    if verdict is True:
        return ("Es action title", "ok")
    if verdict is False:
        return ("No es action title", "crit")
    return ("Verificar", "warn")


def _so_what_pill(verdict: bool | None) -> tuple[str, str]:
    if verdict is True:
        return ("Presente", "ok")
    if verdict is False:
        return ("Ausente", "crit")
    return ("Verificar", "warn")


def _cause_consequence_pill(verdict: bool | None) -> tuple[str, str]:
    if verdict is True:
        return ("OK", "ok")
    if verdict is False:
        return ("Invertido", "crit")
    return ("Solo con API", "muted")


def _text_length_pill(ok: bool | None) -> tuple[str, str]:
    if ok is True:
        return ("OK", "ok")
    if ok is False:
        return ("Revisar", "crit")
    return ("—", "muted")


def _status_pill_data(ok) -> tuple[str, str]:
    if ok is None:
        return ("—", "muted")
    return ("OK", "ok") if ok else ("Revisar", "crit")


def _footer_pill(footer: dict) -> tuple[str, str]:
    if not footer.get("present"):
        return ("Sin pie de página", "muted")
    matches = footer.get("matches_canonical")
    aligned = footer.get("aligned")
    if matches is True and aligned:
        return ("Canónico · OK", "ok")
    if matches is False:
        return ("Texto distinto", "warn")
    if aligned is False:
        return ("Posición off", "warn")
    return ("OK", "ok")


overview = result["deck_overview"]
slides = result["slides"]
total = len(slides)
avg_score = sum(s["score"] for s in slides if s["score"] is not None) / max(
    1, sum(1 for s in slides if s["score"] is not None)
)
role_counts: dict[str, int] = {}
for s in slides:
    r = s.get("role", "unknown")
    role_counts[r] = role_counts.get(r, 0) + 1

# Severity counts
sev_counts: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
for s in slides:
    sev = s.get("severity") or severity_for(s.get("score"))
    sev_counts[sev] = sev_counts.get(sev, 0) + 1


# ---------------------------------------------------------------------------
# Summary header
# ---------------------------------------------------------------------------

st.markdown("---")
provider_label = PROVIDER_LABELS.get(result.get("provider", ""), result.get("provider", "—"))
st.markdown(f"## {file_name}")
st.caption(f"Provider · {provider_label}  ·  Modo · {result['mode']}")

# Severity-first metrics row
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Slides", total)
m2.metric(
    f"{SEVERITY_EMOJI['critical']} Critical",
    sev_counts["critical"],
    delta=f"-{sev_counts['critical']}" if sev_counts["critical"] else "0",
    delta_color="inverse",
    help="Score 0-4 · arreglar primero",
)
m3.metric(
    f"{SEVERITY_EMOJI['warning']} Warning",
    sev_counts["warning"],
    delta=f"-{sev_counts['warning']}" if sev_counts["warning"] else "0",
    delta_color="inverse",
    help="Score 5-7 · should fix",
)
m4.metric(
    f"{SEVERITY_EMOJI['nit']} Nit",
    sev_counts["nit"],
    help="Score 8-9 · polish opcional",
)
if "actual_cost" in result:
    m5.metric("Costo real", f"${result['actual_cost']['total_usd']:.3f}")
else:
    m5.metric("Costo", "$0 · local")

# Compact secondary stats
secondary = []
secondary.append(f"Score promedio · **{avg_score:.1f}**/10")
secondary.append(f"{SEVERITY_EMOJI['ok']} OK · {sev_counts['ok']}")
if overview.get("skipped_slides"):
    secondary.append(f"Skipped · {len(overview['skipped_slides'])}")
st.caption("  ·  ".join(secondary))


# ---------------------------------------------------------------------------
# Cost — estimated vs actual
# ---------------------------------------------------------------------------

if "actual_cost" in result and est is not None:
    st.markdown("")
    styles.section_label("Costo · estimado vs real")

    ac = result["actual_cost"]
    diff_total = ac["total_usd"] - est["total_usd"]
    diff_pct = (diff_total / est["total_usd"] * 100) if est["total_usd"] > 0 else 0

    styles.cost_panel(
        "Costo real",
        f"${ac['total_usd']:.4f}",
        sub=(
            f"Estimado ${est['total_usd']:.4f}  ·  "
            f'<span class="qa-cost-panel-accent">{diff_pct:+.0f}%</span> vs estimado'
        ),
    )

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Per slide (real)", f"${ac['per_slide_usd']:.4f}")
    cc2.metric("Storyline (real)", f"${ac['storyline_usd']:.4f}")
    if ac.get("visual_usd", 0) > 0:
        cc3.metric("Visual (real)", f"${ac['visual_usd']:.4f}")
    else:
        cc3.metric("Visual", "—")

    with st.expander("Detalle por etapa"):
        rows = [
            {
                "Etapa": "Per slide",
                "Estimado": f"${est['per_slide_usd']:.4f}",
                "Real": f"${ac['per_slide_usd']:.4f}",
                "Δ": f"{(ac['per_slide_usd'] - est['per_slide_usd']):+.4f}",
            },
            {
                "Etapa": "Storyline",
                "Estimado": f"${est['storyline_usd']:.4f}",
                "Real": f"${ac['storyline_usd']:.4f}",
                "Δ": f"{(ac['storyline_usd'] - est['storyline_usd']):+.4f}",
            },
            {
                "Etapa": "Visual",
                "Estimado": f"${est['visual_usd']:.4f}",
                "Real": f"${ac['visual_usd']:.4f}",
                "Δ": f"{(ac['visual_usd'] - est['visual_usd']):+.4f}",
            },
            {
                "Etapa": "Total",
                "Estimado": f"${est['total_usd']:.4f}",
                "Real": f"${ac['total_usd']:.4f}",
                "Δ": f"{diff_total:+.4f}",
            },
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

st.markdown("")
tab_overview, tab_slides, tab_storyline, tab_visual, tab_usage, tab_export = st.tabs(
    ["Deck overview", "Por slide", "Storyline", "Visión", "Tokens", "Export"]
)


# -------- Deck overview --------
with tab_overview:
    def _check_card(title: str, ok, notes: str, extra=None):
        with st.container(border=True):
            cols = st.columns([4, 1])
            cols[0].markdown(f"**{title}**")
            cols[1].markdown(_status_pill(ok), unsafe_allow_html=True)
            st.caption(notes)
            if extra is not None:
                extra()

    fa = overview["filename_alignment_detail"]
    _check_card("Filename ↔ títulos", fa["ok"], fa["notes"])

    sub = overview["subtitle_filename_alignment_detail"]
    def _subs():
        if sub.get("subtitles"):
            with st.expander("Subtítulos detectados"):
                for s in sub["subtitles"]:
                    st.markdown(f"- Slide {s['slide_number']} · `{s['text']}`")
    _check_card("Filename ↔ subtítulos", sub["ok"], sub["notes"], _subs)

    fa_geom = overview["footer_alignment_detail"]
    def _footer_geom_extra():
        if fa_geom.get("findings"):
            with st.expander(f"Posiciones detectadas · {len(fa_geom['findings'])} slides"):
                st.dataframe(
                    [
                        {
                            "Slide": f["slide_number"],
                            "Top (in)": f["top_in"],
                            "Left (in)": f.get("left_in"),
                            "Height (in)": f["height_in"],
                            "Texto": f["text"],
                        }
                        for f in fa_geom["findings"]
                    ],
                    use_container_width=True, hide_index=True,
                )
    _check_card("Pie de página · alineación", fa_geom.get("ok"), fa_geom.get("notes", "—"), _footer_geom_extra)

    ftc = overview["footer_text_consistency_detail"]
    def _footer_text_extra():
        if ftc.get("variations") and len(ftc.get("variations", [])) > 1:
            with st.expander(f"Variantes detectadas · {len(ftc['variations'])}"):
                st.dataframe(
                    [{"Texto": v["text"], "Slides": v["count"]} for v in ftc["variations"]],
                    use_container_width=True, hide_index=True,
                )
        if ftc.get("coverage_pct") is not None:
            cov_pct = ftc["coverage_pct"] * 100
            st.caption(
                f"Cobertura · {ftc.get('content_with_footer', 0)}/{ftc.get('content_slides', 0)} "
                f"slides de contenido tienen pie de página ({cov_pct:.0f}%)."
            )
    _check_card("Pie de página · texto consistente", ftc.get("ok"), ftc.get("notes", "—"), _footer_text_extra)

    fmt = overview["footer_matches_deck_title_detail"]
    def _footer_match_extra():
        if fmt.get("cover_title"):
            st.caption(f"Título de la portada · `{fmt['cover_title']}`")
        if fmt.get("matching_slides"):
            st.caption(f"Slides que repiten el título · {fmt['matching_slides']}")
    _check_card("Pie de página · repite el título del deck", fmt.get("ok"), fmt.get("notes", "—"), _footer_match_extra)

    caps = overview["footer_caps_detail"]
    def _caps_extra():
        if caps.get("outliers"):
            with st.expander(f"Outliers · {len(caps['outliers'])}"):
                st.dataframe(
                    [{"Slide": o["slide_number"], "Estilo": o["style"], "Texto": o["text"]} for o in caps["outliers"]],
                    use_container_width=True, hide_index=True,
                )
    _check_card("Pie de página · caps consistency", caps.get("ok"), caps.get("notes", "—"), _caps_extra)

    tfc = overview["title_format_consistency_detail"]
    def _tfc_extra():
        counts = tfc.get("counts", {})
        cc = st.columns(4)
        cc[0].metric("Sin título", counts.get("empty", 0))
        cc[1].metric("Cortos", counts.get("short", 0))
        cc[2].metric("Medianos", counts.get("medium", 0))
        cc[3].metric("Largos", counts.get("long", 0))
    _check_card("Formato de títulos", tfc.get("ok"), tfc.get("notes", "—"), _tfc_extra)

    dup = overview["duplicate_titles_detail"]
    def _dup_extra():
        if dup.get("duplicates"):
            for d in dup["duplicates"]:
                slides_str = ", ".join(str(n) for n in d["slide_numbers"])
                st.markdown(f"Slides **{slides_str}** · `{d['title']}`")
    _check_card("Títulos duplicados", dup.get("ok"), dup.get("notes", "—"), _dup_extra)

    with st.container(border=True):
        st.markdown("**Distribución de roles**")
        rcols = st.columns(max(1, len(role_counts)))
        for i, (r, c) in enumerate(sorted(role_counts.items(), key=lambda x: -x[1])):
            rcols[i].metric(r, c)


# -------- Per slide --------
with tab_slides:
    # Severity filter — multi-select with counts. Defaults to showing critical+warning only.
    styles.section_label("Filtrar por severidad")
    sev_cols = st.columns(4)
    show_sev: dict[str, bool] = {}
    sev_defaults = {"critical": True, "warning": True, "nit": False, "ok": False}
    for i, sev in enumerate(SEVERITY_ORDER):
        with sev_cols[i]:
            label = f"{SEVERITY_EMOJI[sev]} {SEVERITY_LABELS[sev]} ({sev_counts[sev]})"
            show_sev[sev] = st.checkbox(label, value=sev_defaults[sev], key=f"sev_{sev}")

    st.markdown("")
    f1, f2, f3 = st.columns(3)
    hide_skipped = f1.checkbox("Ocultar skipped", value=False)
    role_filter = f2.multiselect("Filtrar role", options=sorted(role_counts.keys()), default=[])
    expand_all = f3.checkbox("Expandir todos", value=False)

    visible = [
        s for s in slides
        if show_sev.get(s.get("severity") or severity_for(s.get("score")), False)
        and (not hide_skipped or not s.get("_skipped"))
        and (not role_filter or s.get("role") in role_filter)
    ]
    st.caption(f"Mostrando {len(visible)} de {total} slides")
    st.markdown("")

    for slide in visible:
        n = slide["slide_number"]
        score = slide["score"]
        sev = slide.get("severity") or severity_for(score)
        role = slide.get("role", "?")
        skipped_tag = " · skipped" if slide.get("_skipped") else ""
        title = slide["action_title"].get("current_title") or "(sin título)"
        title_disp = (title[:70] + "…") if len(title) > 70 else title

        score_text = f"{score}/10" if score is not None else "—"
        sev_label = f"{SEVERITY_EMOJI[sev]} {SEVERITY_LABELS[sev].upper()}"
        header = f"{sev_label}  ·  Slide {n}  ·  {score_text}  ·  {role}{skipped_tag}  ·  {title_disp}"
        # Default expanded: critical only. User can toggle "Expandir todos".
        expanded = expand_all or sev == "critical"

        with st.expander(header, expanded=expanded):
            # Thumbnail (if rendered) — show above the summary
            thumb_bytes = thumbs.get(n) if thumbs else None
            if thumb_bytes:
                tc1, tc2 = st.columns([1, 2])
                with tc1:
                    st.image(thumb_bytes, use_container_width=True)
                with tc2:
                    st.markdown(f"*{slide['summary']}*")
            else:
                st.markdown(f"*{slide['summary']}*")
            st.markdown("")
            cols = st.columns(2)

            # ── LEFT column: semantic checks ──
            with cols[0]:
                at = slide["action_title"]
                pill_text, pill_var = _action_title_pill(at.get("is_action_title"))
                styles.check_block(
                    "Action title",
                    pill_text, pill_var,
                    current_value=at.get("current_title") or "(sin título)",
                    notes=at.get("notes"),
                    suggestion=at.get("suggestion"),
                )

                sw = slide["so_what"]
                pill_text, pill_var = _so_what_pill(sw.get("present"))
                styles.check_block(
                    "So-what",
                    pill_text, pill_var,
                    notes=sw.get("notes"),
                    suggestion=sw.get("suggestion"),
                )

                cc = slide["cause_consequence"]
                pill_text, pill_var = _cause_consequence_pill(cc.get("ok"))
                styles.check_block(
                    "Causa → consecuencia",
                    pill_text, pill_var,
                    notes=cc.get("notes"),
                )

            # ── RIGHT column: structural checks ──
            with cols[1]:
                tl = slide["text_length"]
                pill_text, pill_var = _text_length_pill(tl.get("ok"))
                long_paras_md = ""
                if tl.get("long_paragraphs"):
                    long_paras_md = "Párrafos problemáticos:\n" + "\n".join(
                        f"• {p}" for p in tl["long_paragraphs"]
                    )
                notes_combined = tl.get("notes", "")
                if long_paras_md:
                    notes_combined = (notes_combined + "\n\n" + long_paras_md).strip()
                styles.check_block(
                    "Longitud de párrafos",
                    pill_text, pill_var,
                    notes=notes_combined,
                    suggestion=tl.get("suggestion"),
                )

                footer = slide["footer"]
                pill_text, pill_var = _footer_pill(footer)
                # Build informative notes for the footer
                footer_notes_parts = [footer.get("notes", "")]
                canonical = footer.get("canonical_text")
                matches = footer.get("matches_canonical")
                if footer.get("present") and canonical:
                    if matches is True:
                        footer_notes_parts.append(
                            f"Coincide con el footer canónico del deck."
                        )
                    elif matches is False:
                        footer_notes_parts.append(
                            f"El footer canónico del deck es: \"{canonical}\". "
                            f"Este slide usa un texto distinto."
                        )
                footer_suggestion = None
                if not footer.get("present") and canonical:
                    footer_suggestion = (
                        f"Agregar el footer canónico del deck: \"{canonical}\"."
                    )
                elif matches is False and canonical:
                    footer_suggestion = (
                        f"Reemplazar el footer de este slide por el canónico: \"{canonical}\"."
                    )
                styles.check_block(
                    "Pie de página",
                    pill_text, pill_var,
                    current_value=footer.get("current_footer") if footer.get("present") else None,
                    notes=" ".join(p for p in footer_notes_parts if p).strip() or None,
                    suggestion=footer_suggestion,
                )

            # Visual block (full column)
            if slide.get("visual"):
                v = slide["visual"]
                vq = v.get("visual_quality", {})
                cr = v.get("chart_readability", {})
                vq_pill_text, vq_pill_var = _status_pill_data(vq.get("ok"))
                styles.check_block(
                    "Análisis visual",
                    vq_pill_text, vq_pill_var,
                    notes=vq.get("notes"),
                    suggestion=vq.get("suggestion"),
                )
                if cr.get("present"):
                    cr_pill_text, cr_pill_var = _status_pill_data(cr.get("ok"))
                    styles.check_block(
                        "Chart readability",
                        cr_pill_text, cr_pill_var,
                        notes=cr.get("notes"),
                        suggestion=cr.get("suggestion"),
                    )
                if v.get("design_issues"):
                    issues_md = "\n".join(f"• {issue}" for issue in v["design_issues"])
                    styles.check_block(
                        "Issues de diseño",
                        f"{len(v['design_issues'])}", "warn",
                        notes=issues_md,
                    )


# -------- Storyline --------
with tab_storyline:
    if overview.get("storyline_coherent") is None:
        st.info("Storyline requiere modo full.")
    else:
        s1, s2 = st.columns([5, 1])
        s1.markdown("### Storyline coherente")
        s2.markdown(_status_pill(overview["storyline_coherent"]), unsafe_allow_html=True)
        st.markdown(overview.get("storyline_notes", "—"))
        st.caption(f"Filename ↔ títulos · {overview.get('filename_subtitle_alignment', '—')}")

        cross = overview.get("cross_slide_issues") or []
        st.markdown("")
        st.markdown(f"### Issues cross-slide · {len(cross)}")
        if not cross:
            st.success("Sin issues cross-slide.")
        else:
            for issue in cross:
                slides_str = ", ".join(str(s) for s in issue["slide_numbers"])
                st.markdown(f"- Slides **{slides_str}** · {issue['issue']}")

        st.markdown("")
        styles.section_label("Secuencia de action titles")
        st.dataframe(
            [
                {
                    "Slide": s["slide_number"],
                    "Score": s["score"],
                    "Es action title": s["action_title"].get("is_action_title"),
                    "Título": s["action_title"].get("current_title"),
                }
                for s in slides
            ],
            use_container_width=True, hide_index=True,
        )


# -------- Visual --------
with tab_visual:
    if not overview.get("visual_analysis_enabled"):
        st.info("Análisis visual no activado en esta corrida.")
    else:
        visual_slides_data = [s for s in slides if s.get("visual")]
        if not visual_slides_data:
            st.info("Visual activo pero no se encontraron slides con imágenes.")
        else:
            styles.section_label(f"{len(visual_slides_data)} slides con análisis visual")
            for slide in visual_slides_data:
                n = slide["slide_number"]
                v = slide["visual"]
                vq = v.get("visual_quality", {})
                cr = v.get("chart_readability", {})
                with st.container(border=True):
                    h1, h2 = st.columns([5, 1])
                    h1.markdown(f"**Slide {n}** · {slide['action_title'].get('current_title', '')}")
                    h2.markdown(_status_pill(vq.get("ok")), unsafe_allow_html=True)
                    st.caption(vq.get("notes", "—"))
                    if cr.get("present"):
                        st.markdown(f"Chart · {cr.get('notes','—')}")
                    if v.get("design_issues"):
                        for issue in v["design_issues"]:
                            st.markdown(f"- {issue}")


# -------- Tokens --------
with tab_usage:
    if "usage" not in result:
        st.info("Token usage solo en modo full.")
    else:
        u = result["usage"]
        models = result.get("models", {})

        def _usage_row(label: str, model_id: str, key: str):
            st.markdown(f"### {label}  ·  `{model_id}`")
            d = u[key]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Input", f"{d['input']:,}")
            c2.metric("Cache write", f"{d['cache_write']:,}")
            c3.metric("Cache read", f"{d['cache_read']:,}")
            c4.metric("Output", f"{d['output']:,}")
            st.markdown("")

        _usage_row("Per slide", models.get("per_slide", "?"), "per_slide")
        _usage_row("Storyline", models.get("storyline", "?"), "storyline")
        if u.get("visual", {}).get("input", 0):
            _usage_row("Visual", models.get("visual", "?"), "visual")
        st.markdown("---")
        with st.expander("Usage raw JSON"):
            st.json(u)


# -------- Export --------
with tab_export:
    json_data = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
    c1, c2 = st.columns(2)
    c1.download_button(
        "Descargar JSON",
        data=json_data,
        file_name=f"{Path(file_name).stem}_qa_report.json",
        mime="application/json",
        use_container_width=True,
    )

    def _build_md() -> str:
        provider_str = result.get("provider", "local")
        models_str = result.get("models", {})
        lines: list[str] = [
            f"# Reporte QA · {file_name}",
            f"_Provider: **{provider_str}** · "
            f"Per-slide: `{models_str.get('per_slide','—')}` · "
            f"Storyline: `{models_str.get('storyline','—')}`_",
            f"_Slides: {total} · Score promedio: {avg_score:.1f}/10_",
        ]
        if "actual_cost" in result:
            lines.append(f"_Costo real: **${result['actual_cost']['total_usd']:.4f}**_")
        lines.append("\n## Vista global\n")
        lines.append(f"- **Storyline coherente:** {overview.get('storyline_coherent')}")
        lines.append(f"  - {overview.get('storyline_notes', '—')}")
        lines.append(f"- **Filename ↔ títulos:** {overview['filename_alignment_detail']['notes']}")
        lines.append(f"- **Filename ↔ subtítulos:** {overview['subtitle_filename_alignment_detail']['notes']}")
        lines.append(f"- **Pie de página · alineación:** {overview['footer_alignment_detail'].get('notes', '—')}")
        lines.append(f"- **Pie de página · texto consistente:** {overview['footer_text_consistency_detail'].get('notes', '—')}")
        lines.append(f"- **Pie de página · repite título del deck:** {overview['footer_matches_deck_title_detail'].get('notes', '—')}")
        lines.append(f"- **Pie de página · caps:** {overview['footer_caps_detail'].get('notes', '—')}")
        lines.append(f"- **Formato títulos:** {overview['title_format_consistency_detail'].get('notes', '—')}")
        lines.append(f"- **Duplicados:** {overview['duplicate_titles_detail'].get('notes', '—')}")
        if overview.get("cross_slide_issues"):
            lines.append("\n### Cross-slide\n")
            for issue in overview["cross_slide_issues"]:
                s_str = ", ".join(str(s) for s in issue["slide_numbers"])
                lines.append(f"- Slides {s_str}: {issue['issue']}")
        lines.append("\n## Resumen de severidad\n")
        lines.append(
            f"- 🔴 Critical · {sev_counts['critical']}  ·  "
            f"🟡 Warning · {sev_counts['warning']}  ·  "
            f"🔵 Nit · {sev_counts['nit']}  ·  "
            f"🟢 OK · {sev_counts['ok']}"
        )
        lines.append("\n## Slides\n")
        for slide in slides:
            score_str = f"{slide['score']}/10" if slide["score"] is not None else "—"
            sev = slide.get("severity") or severity_for(slide.get("score"))
            sev_label = f"{SEVERITY_EMOJI.get(sev,'')} {SEVERITY_LABELS.get(sev,'')}"
            lines.append(f"### {sev_label} · Slide {slide['slide_number']} · {score_str} ({slide.get('role','?')})")
            lines.append(f"_{slide['summary']}_\n")
            at = slide["action_title"]
            lines.append(f"**Título:** `{at.get('current_title','')}`")
            lines.append(f"- Action title ({at.get('is_action_title')}): {at.get('notes','')}")
            if at.get("suggestion"):
                lines.append(f"  - Sugerencia: {at['suggestion']}")
            sw = slide["so_what"]
            lines.append(f"- So-what ({sw.get('present')}): {sw.get('notes','')}")
            if sw.get("suggestion"):
                lines.append(f"  - Sugerencia: {sw['suggestion']}")
            cc = slide["cause_consequence"]
            lines.append(f"- Causa→consecuencia ({cc.get('ok')}): {cc.get('notes','')}")
            tl = slide["text_length"]
            lines.append(f"- Largo de párrafos ({tl.get('ok')}): {tl.get('notes','')}")
            for p in tl.get("long_paragraphs", []):
                lines.append(f"  - > {p}")
            if slide.get("visual"):
                v = slide["visual"]
                lines.append(f"- Visual ({v['visual_quality'].get('ok')}): {v['visual_quality'].get('notes','')}")
                for issue in v.get("design_issues", []):
                    lines.append(f"  - {issue}")
            lines.append("")
        return "\n".join(lines)

    md_data = _build_md().encode("utf-8")
    c2.download_button(
        "Descargar Markdown",
        data=md_data,
        file_name=f"{Path(file_name).stem}_qa_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.markdown("")
    styles.section_label("Preview Markdown")
    st.code(md_data.decode("utf-8")[:3000] + ("…" if len(md_data) > 3000 else ""), language="markdown")
