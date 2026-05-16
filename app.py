"""PPT QA Agent — Streamlit web app (simplified, checklist-style)."""

from __future__ import annotations

import hashlib
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
from renderer import cache_key_for, render


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PPT QA Agent",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
styles.inject()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

styles.eyebrow("Auditoría de presentaciones")
st.markdown("# Tu deck, revisado slide por slide")
st.markdown(
    '<p style="color: var(--text-muted); font-size: 0.95rem; max-width: 62ch; '
    'margin: -0.3rem 0 1rem 0; line-height: 1.5;">'
    "Subí un <code>.pptx</code> y obtené un checklist de calidad por slide. "
    "Si configurás una API key, el análisis usa Claude o GPT-4o para juicios "
    "semánticos. Sin key corre el modo local (gratis, solo checks estructurales)."
    '</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar — only API keys + scope info
# ---------------------------------------------------------------------------

PROVIDER_LABELS = {
    "claude": "Claude — Sonnet 4.6 + Opus 4.7",
    "openai": "OpenAI — GPT-4o",
}

all_keys = load_all_keys()
keys_status: dict[str, tuple[str | None, str]] = {p: all_keys.get(p, (None, "")) for p in PROVIDERS}
available_providers = [p for p, (k, _) in keys_status.items() if k]

with st.sidebar:
    styles.section_label("API keys")
    for p in PROVIDERS:
        key, source = keys_status.get(p, (None, ""))
        label = PROVIDER_LABELS.get(p, p)
        if key:
            st.markdown(f"**{label}**")
            st.markdown(styles.pill(f"{mask(key)} · {source}", "ok"), unsafe_allow_html=True)
        else:
            st.markdown(f"**{label}**")
            st.markdown(styles.pill("Sin key", "muted"), unsafe_allow_html=True)
        st.markdown("")

    with st.expander("Configurar key manualmente"):
        for p in PROVIDERS:
            env_var = "ANTHROPIC_API_KEY" if p == "claude" else "OPENAI_API_KEY"
            manual = st.text_input(
                f"{PROVIDER_LABELS[p]} ({env_var})",
                type="password",
                key=f"manual_{p}",
                placeholder="sk-...",
            )
            if manual:
                keys_status[p] = (manual.strip(), "input manual")
        # Re-derive available providers after manual input
        available_providers = [p for p, (k, _) in keys_status.items() if k]

    st.markdown("---")
    styles.section_label("Qué evalúa")
    st.markdown(
        "**Local** (sin API)  \n"
        "Largo de párrafos · pie de página · slide role · filename ↔ títulos · "
        "formato de títulos · duplicados.\n\n"
        "**Full** (con API)  \n"
        "↑ todo eso **+** action title quality · so-what · "
        "causa→consecuencia · storyline · análisis visual (opcional)."
    )


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

uploaded = st.file_uploader(
    "Subí tu presentación", type=["pptx"], label_visibility="collapsed"
)

if uploaded is None:
    for k in list(st.session_state.keys()):
        if k.startswith(("qa_result", "qa_est", "qa_file_hash", "qa_thumbs")):
            del st.session_state[k]
    st.markdown("")
    st.info("Esperando un `.pptx`. El modo local no gasta tokens.")
    st.stop()


# Stable file hash for caching across reruns
_file_bytes = uploaded.getvalue()
file_hash = hashlib.sha1(_file_bytes).hexdigest()[:16]

with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
    tmp.write(_file_bytes)
    tmp_path = Path(tmp.name)

# Cache extracted deck
deck_cache_key = f"deck__{file_hash}"
try:
    if deck_cache_key in st.session_state:
        deck = st.session_state[deck_cache_key]
    else:
        with st.spinner("Extrayendo contenido..."):
            deck = extract_deck(tmp_path)
        st.session_state[deck_cache_key] = deck
except Exception as e:
    st.error(f"Error al extraer: {e}")
    try:
        tmp_path.unlink()
    except OSError:
        pass
    st.stop()

# Clear cached result if a different file was uploaded
if st.session_state.get("qa_file_hash") and st.session_state["qa_file_hash"] != file_hash:
    for k in ("qa_result", "qa_est"):
        st.session_state.pop(k, None)
st.session_state["qa_file_hash"] = file_hash

file_name = uploaded.name
slides_with_visuals = [s for s in deck["slides"] if s.get("has_visuals")]
n_visuals = len(slides_with_visuals)


# ---------------------------------------------------------------------------
# Thumbnail loader — always auto (LibreOffice → PowerPoint → schematic)
# ---------------------------------------------------------------------------

def _get_thumbnails(pptx_path: Path, deck: dict) -> dict[int, bytes]:
    """Always render thumbnails using best available backend."""
    key = f"thumbs__{cache_key_for(pptx_path)}"
    if key in st.session_state:
        return st.session_state[key]

    thumbs: dict[int, bytes] = {}
    progress = st.progress(0.0, text="Renderizando miniaturas…")
    try:
        thumbs, used_mode = render(
            pptx_path=pptx_path,
            deck=deck,
            mode="auto",
            progress_cb=lambda done, total: progress.progress(
                done / max(1, total),
                text=f"Renderizando miniaturas ({used_mode_safe()}) · {done}/{total}",
            ) if False else progress.progress(done / max(1, total)),
        )
        st.session_state[f"thumbs_mode__{cache_key_for(pptx_path)}"] = used_mode
    except Exception as e:
        st.caption(f"Sin miniaturas: {e}")
        thumbs = {}
    finally:
        progress.empty()

    st.session_state[key] = thumbs
    return thumbs


def used_mode_safe():
    return "auto"


# Compact deck summary
st.markdown("")
c1, c2 = st.columns(2)
c1.metric("Slides", deck["slide_count"])
c2.metric("Con imágenes", n_visuals)

with st.expander("Ver contenido extraído"):
    st.json(deck, expanded=False)


# ---------------------------------------------------------------------------
# Provider selector (main page) — only when at least one key is configured
# ---------------------------------------------------------------------------

st.markdown("")
selected_provider: str | None = None
api_key: str | None = None
mode = "local"

if available_providers:
    styles.section_label("Modelo")
    selected_provider = st.radio(
        "Modelo",
        options=available_providers,
        format_func=lambda p: PROVIDER_LABELS.get(p, p),
        horizontal=True,
        label_visibility="collapsed",
    )
    api_key, _ = keys_status[selected_provider]
    mode = "full"
else:
    st.info(
        "Sin API key configurada. Vas a correr en **modo local** (gratis, "
        "solo checks estructurales). Para análisis semántico configurá una "
        "key en el sidebar."
    )


# ---------------------------------------------------------------------------
# Run options + cost estimate
# ---------------------------------------------------------------------------

slides_to_process = deck["slide_count"]
skip_roles: set[str] | None = None
visual_enabled = False
workers = 6
deck_to_run = deck
est = None

if mode == "full":
    st.markdown("")
    styles.section_label("Opciones de la corrida")
    o1, o2 = st.columns(2)
    with o1:
        analyze_all = st.checkbox(
            "Evaluar todos los slides (sin skip)",
            value=False,
            help=f"Por defecto se saltean {sorted(DEFAULT_SKIP_ROLES)}.",
        )
        skip_roles = set() if analyze_all else set(DEFAULT_SKIP_ROLES)

        visual_enabled = st.checkbox(
            f"Analizar charts / imágenes ({n_visuals} con imagen)",
            value=False,
            disabled=(n_visuals == 0),
        )
    with o2:
        smoke_test = st.checkbox("Smoke test (solo primeros N)", value=False)
        if smoke_test:
            slides_to_process = st.slider(
                "N slides", min_value=1, max_value=deck["slide_count"],
                value=min(5, deck["slide_count"]),
            )

    if slides_to_process < deck["slide_count"]:
        deck_to_run = {
            **deck,
            "slides": deck["slides"][:slides_to_process],
            "slide_count": slides_to_process,
        }

    from checks import classify_slide_role
    will_skip = sum(
        1 for s in deck_to_run["slides"]
        if classify_slide_role(s) in (skip_roles or set())
    )
    will_visual = (
        sum(1 for s in deck_to_run["slides"] if s.get("has_visuals"))
        if visual_enabled else 0
    )

    est = estimate_cost(
        deck_to_run["slide_count"],
        skipped_count=will_skip,
        visual_slide_count=will_visual,
        provider=selected_provider,
    )

    st.caption(
        f"Costo estimado · **${est['total_usd']:.3f}** "
        f"({selected_provider}, {est['analyzed_count']} slides, "
        f"~${est['visual_usd']:.3f} visión)"
    )


# ---------------------------------------------------------------------------
# Run button
# ---------------------------------------------------------------------------

if mode == "local":
    run_label = "Correr análisis local"
elif mode == "full" and api_key:
    run_label = (
        f"Correr con {PROVIDER_LABELS[selected_provider]}  ·  "
        f"{deck_to_run['slide_count']} slides  ·  ~${est['total_usd']:.3f}"
    )
else:
    run_label = "Configurá la API key primero"

can_run = (mode == "local") or (mode == "full" and api_key)

st.markdown("")
run_button = st.button(run_label, type="primary", use_container_width=True, disabled=not can_run)


# ---------------------------------------------------------------------------
# Pipeline run
# ---------------------------------------------------------------------------

if run_button:
    images_by_slide: dict | None = None
    if mode == "full" and visual_enabled:
        with st.spinner("Extrayendo imágenes..."):
            images_by_slide = extract_images(tmp_path)
            if slides_to_process < deck["slide_count"]:
                images_by_slide = {
                    n: imgs for n, imgs in images_by_slide.items()
                    if n <= slides_to_process
                }

    # Render thumbnails — ALWAYS (auto backend)
    thumbs = _get_thumbnails(tmp_path, deck_to_run)

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

    st.markdown("---")
    styles.section_label("Progreso")
    status_box = st.empty()
    progress_bar = st.empty()
    live_table = st.empty()

    completed_slides: list[dict] = []
    result_obj = None
    error = None

    def _render_live_table():
        if not completed_slides:
            return
        rows = []
        for entry in completed_slides:
            f = entry["finding"]
            title = f.get("action_title", {}).get("current_title", "")
            title_disp = (title[:60] + "…") if len(title) > 60 else title
            sev = f.get("severity") or severity_for(f.get("score"))
            rows.append({
                "": SEVERITY_EMOJI.get(sev, "·"),
                "Slide": entry["slide_number"],
                "Score": f"{f.get('score', '?')}/10",
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
                text=f"{payload['completed']} / {payload['total']} slides",
            )
            _render_live_table()
        elif kind == "visual_done":
            status_box.info(f"Visión · {payload['completed']} / {payload['total']}")
        elif kind == "error":
            error = payload
            break
        elif kind == "result":
            result_obj = payload

    if error:
        status_box.error(f"Error · {error}")
        st.stop()
    if result_obj is None:
        status_box.error("No se recibió resultado.")
        st.stop()

    status_box.success("Análisis completo.")
    progress_bar.empty()
    live_table.empty()

    st.session_state["qa_result"] = result_obj
    st.session_state["qa_est"] = est
    st.session_state["qa_thumbs"] = thumbs

else:
    try:
        tmp_path.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Read result from session_state
# ---------------------------------------------------------------------------

result = st.session_state.get("qa_result")
if result is None:
    st.stop()

if est is None:
    est = st.session_state.get("qa_est")
thumbs = st.session_state.get("qa_thumbs", {})


# ---------------------------------------------------------------------------
# Results: single scrolling page (no tabs)
# ---------------------------------------------------------------------------

overview = result["deck_overview"]
slides = result["slides"]
total = len(slides)
avg_score = sum(s["score"] for s in slides if s["score"] is not None) / max(
    1, sum(1 for s in slides if s["score"] is not None)
)
sev_counts: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
for s in slides:
    sev = s.get("severity") or severity_for(s.get("score"))
    sev_counts[sev] = sev_counts.get(sev, 0) + 1
role_counts: dict[str, int] = {}
for s in slides:
    r = s.get("role", "unknown")
    role_counts[r] = role_counts.get(r, 0) + 1


# Top metrics
st.markdown("---")
provider_label = PROVIDER_LABELS.get(result.get("provider", ""), result.get("provider", "—"))
st.markdown(f"## {file_name}")
st.caption(f"Provider · {provider_label}  ·  Modo · {result['mode']}")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Slides", total)
m2.metric(f"{SEVERITY_EMOJI['critical']} Critical", sev_counts["critical"])
m3.metric(f"{SEVERITY_EMOJI['warning']} Warning", sev_counts["warning"])
m4.metric(f"{SEVERITY_EMOJI['nit']} Nit", sev_counts["nit"])
if "actual_cost" in result:
    m5.metric("Costo real", f"${result['actual_cost']['total_usd']:.3f}")
else:
    m5.metric("Costo", "$0 · local")

st.caption(
    f"Score promedio · **{avg_score:.1f}**/10  ·  "
    f"{SEVERITY_EMOJI['ok']} OK · {sev_counts['ok']}"
    + (f"  ·  Skipped · {len(overview.get('skipped_slides', []))}"
       if overview.get('skipped_slides') else "")
)


# Cost estimate vs actual (if available)
if "actual_cost" in result and est is not None:
    st.markdown("")
    ac = result["actual_cost"]
    diff_pct = (
        (ac["total_usd"] - est["total_usd"]) / est["total_usd"] * 100
        if est["total_usd"] > 0 else 0
    )
    styles.cost_panel(
        "Costo real",
        f"${ac['total_usd']:.4f}",
        sub=(
            f"Estimado ${est['total_usd']:.4f}  ·  "
            f'<span class="qa-cost-panel-accent">{diff_pct:+.0f}%</span> vs estimado  ·  '
            f"Per slide ${ac['per_slide_usd']:.4f}  ·  "
            f"Storyline ${ac['storyline_usd']:.4f}  ·  "
            f"Visual ${ac['visual_usd']:.4f}"
        ),
    )


# Severity filter
st.markdown("")
styles.section_label("Filtrar por severidad")
fcols = st.columns(4)
show_sev: dict[str, bool] = {}
for i, sev in enumerate(SEVERITY_ORDER):
    with fcols[i]:
        label = f"{SEVERITY_EMOJI[sev]} {SEVERITY_LABELS[sev]} ({sev_counts[sev]})"
        show_sev[sev] = st.checkbox(label, value=True, key=f"sev_{sev}")

ff1, ff2 = st.columns(2)
hide_skipped = ff1.checkbox("Ocultar skipped", value=False)
role_filter = ff2.multiselect("Filtrar role", options=sorted(role_counts.keys()), default=[])


# Per-slide cards
visible = [
    s for s in slides
    if show_sev.get(s.get("severity") or severity_for(s.get("score")), False)
    and (not hide_skipped or not s.get("_skipped"))
    and (not role_filter or s.get("role") in role_filter)
]
st.markdown("")
st.caption(f"Mostrando {len(visible)} de {total} slides")
st.markdown("")

for slide in visible:
    thumb_bytes = thumbs.get(slide["slide_number"]) if thumbs else None
    st.markdown(
        styles.slide_card_html(slide, thumb_bytes=thumb_bytes),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Secondary sections — collapsed expanders at the bottom
# ---------------------------------------------------------------------------

# Storyline
if overview.get("storyline_coherent") is not None:
    with st.expander("Storyline cross-slide", expanded=False):
        coh = overview.get("storyline_coherent")
        st.markdown(
            "**Storyline coherente:** "
            + (styles.pill("Sí", "ok") if coh else styles.pill("No", "crit")),
            unsafe_allow_html=True,
        )
        st.markdown(overview.get("storyline_notes", "—"))
        st.caption(
            f"Filename ↔ títulos · {overview.get('filename_subtitle_alignment', '—')}"
        )
        cross = overview.get("cross_slide_issues") or []
        if cross:
            st.markdown(f"**Issues cross-slide ({len(cross)}):**")
            for issue in cross:
                slides_str = ", ".join(str(s) for s in issue["slide_numbers"])
                st.markdown(f"- Slides **{slides_str}** · {issue['issue']}")
        else:
            st.success("Sin issues cross-slide.")

# Visual section (only if enabled)
if overview.get("visual_analysis_enabled"):
    visual_slides_data = [s for s in slides if s.get("visual")]
    if visual_slides_data:
        with st.expander(f"Análisis visual · {len(visual_slides_data)} slides", expanded=False):
            for slide in visual_slides_data:
                n = slide["slide_number"]
                v = slide["visual"]
                vq = v.get("visual_quality", {})
                st.markdown(
                    f"**Slide {n}** · "
                    + (styles.pill("OK", "ok") if vq.get("ok") else styles.pill("Revisar", "crit")),
                    unsafe_allow_html=True,
                )
                st.caption(vq.get("notes", "—"))
                if v.get("design_issues"):
                    for issue in v["design_issues"]:
                        st.markdown(f"- {issue}")
                st.markdown("---")

# Token usage
if "usage" in result:
    with st.expander("Uso de tokens", expanded=False):
        u = result["usage"]
        models = result.get("models", {})

        def _usage_row(label: str, model_id: str, key: str):
            st.markdown(f"**{label}** · `{model_id}`")
            d = u[key]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Input", f"{d['input']:,}")
            c2.metric("Cache write", f"{d['cache_write']:,}")
            c3.metric("Cache read", f"{d['cache_read']:,}")
            c4.metric("Output", f"{d['output']:,}")

        _usage_row("Per slide", models.get("per_slide", "?"), "per_slide")
        st.markdown("")
        _usage_row("Storyline", models.get("storyline", "?"), "storyline")
        if u.get("visual", {}).get("input", 0):
            st.markdown("")
            _usage_row("Visual", models.get("visual", "?"), "visual")
