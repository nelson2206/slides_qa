"""Holmes — el detective de tus decks. Streamlit web app."""

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
from sections import detect_sections


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

_LOGO_PATH = Path(__file__).parent / "assets" / "logo.svg"
st.set_page_config(
    page_title="Holmes — Auditoría MBB de presentaciones",
    page_icon=str(_LOGO_PATH) if _LOGO_PATH.exists() else ":mag:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
styles.inject()

# ---------------------------------------------------------------------------
# Open Graph / social-share meta tags
# Streamlit injects these into <body>, not <head>. WhatsApp's scraper only
# reads <head>, so the OG preview there will fall back to whatever Streamlit
# Cloud provides by default. Twitter / Slack / Discord / Telegram are more
# lenient and DO pick up body-level meta. The static og-image.png lives at
# /app/static/og-image.png (Streamlit Cloud auto-serves the static/ folder).
# ---------------------------------------------------------------------------
_OG_IMAGE_URL = "https://nelson2206.github.io/slides_qa/og-image.png"
st.markdown(
    f'''
<meta property="og:title" content="Holmes — El detective de tus decks">
<meta property="og:description" content="Sube tu .pptx y Holmes lo investiga slide por slide: action titles, so-what, storyline, pie de página, análisis visual. Con criterio de senior MBB.">
<meta property="og:image" content="{_OG_IMAGE_URL}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Holmes — El detective de tus decks">
<meta name="twitter:description" content="Auditoría MBB de presentaciones, slide por slide.">
<meta name="twitter:image" content="{_OG_IMAGE_URL}">
''',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Top nav — tabs above the hero so they read as primary navigation
# ---------------------------------------------------------------------------

tab_audit, tab_practices = st.tabs([
    "🔎  Auditar deck",
    "📋  Buenas prácticas",
])

# Render the static best-practices checklist first. Even if the audit flow
# later calls st.stop(), this tab's content is already written to its container.
with tab_practices:
    st.markdown(
        getattr(styles, "best_practices_html", lambda: "")(),
        unsafe_allow_html=True,
    )

# Activate tab_audit for the rest of the script. We rely on __enter__ pushing
# this tab onto Streamlit's container stack so every subsequent st.* call lands
# inside it. The script ends with st.stop() / natural EOF — Streamlit cleans up
# the container stack at the end of the run, so we don't call __exit__.
tab_audit.__enter__()


# ---------------------------------------------------------------------------
# Hero (lives inside the Auditar tab)
# ---------------------------------------------------------------------------

styles.hero(
    "El detective de tus decks",
    "Holmes",
    "Minsaiter, sube un <code>.pptx</code> y Holmes revisará cada slide con IA "
    "para darte feedback.",
    chips=["Action titles", "So-what por slide", "Pie de página", "Storyline", "Análisis visual"],
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
    "Sube tu presentación", type=["pptx"], label_visibility="collapsed"
)

if uploaded is None:
    for k in list(st.session_state.keys()):
        if k.startswith(("qa_result", "qa_est", "qa_file_hash", "qa_thumbs")):
            del st.session_state[k]
    # Defensive getattr: hide_nav was added recently; on Streamlit Cloud the
    # styles module may be cached from before this commit on first request
    # after deploy. Fall back to no-op so the app doesn't crash.
    getattr(styles, "hide_nav", lambda: None)()
    st.stop()


# Stable file hash for caching across reruns
_file_bytes = uploaded.getvalue()
file_hash = hashlib.sha1(_file_bytes).hexdigest()[:16]

# Cache the raw .pptx bytes by hash so the exporter / fixer / comparator can
# read the original deck on later reruns without re-uploading.
st.session_state[f"pptx_bytes__{file_hash}"] = _file_bytes
st.session_state[f"pptx_filename__{file_hash}"] = uploaded.name

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
getattr(styles, "scroll_anchor", lambda *a, **kw: None)("qa-after-upload")
c1, c2 = st.columns(2)
c1.metric("Slides", deck["slide_count"])
c2.metric("Con imágenes", n_visuals)

# Auto-scroll once per uploaded file: bring the metrics + run button into view.
if st.session_state.get("_scrolled_after_upload") != file_hash:
    st.session_state["_scrolled_after_upload"] = file_hash
    getattr(styles, "auto_scroll_to", lambda *a, **kw: None)("qa-after-upload")


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


# ---------------------------------------------------------------------------
# Run options + cost estimate
# ---------------------------------------------------------------------------

slides_to_process = deck["slide_count"]
skip_roles: set[str] | None = None
skip_slide_numbers: set[int] = set()
visual_enabled = False
workers = 6
deck_to_run = deck
est = None
deck_sections = detect_sections(deck)

if mode == "full":
    st.markdown("")
    styles.section_label("Opciones de la corrida")

    # Section picker — only if the deck has a clear index (≥2 dividers)
    if deck_sections:
        n_auto_skip = sum(1 for s in deck_sections if s.get("auto_skip"))
        hint = (
            f'Detecté <strong>{len(deck_sections)} secciones</strong> en el deck. '
            'Desmarcá las que no querés analizar — sus slides se van a saltear sin gastar tokens.'
        )
        if n_auto_skip:
            hint += (
                f' <strong>{n_auto_skip}</strong> arrancan desmarcadas '
                '(carátula, confidencialidad, índice, referencias, CVs, cierre — boilerplate típico).'
            )
        st.markdown(
            f'<p class="qa-section-picker-hint">{hint}</p>',
            unsafe_allow_html=True,
        )
        sec_cols = st.columns(min(3, len(deck_sections)))
        section_selected: list[bool] = []
        for i, sec in enumerate(deck_sections):
            with sec_cols[i % len(sec_cols)]:
                name = sec["name"]
                rng = f"{sec['start']}–{sec['end']}" if sec["start"] != sec["end"] else str(sec["start"])
                tag = " · boilerplate" if sec.get("auto_skip") else ""
                label = f"{name} · slides {rng} ({len(sec['slide_numbers'])}){tag}"
                default_checked = not sec.get("auto_skip", False)
                section_selected.append(
                    st.checkbox(label, value=default_checked, key=f"sec_{i}")
                )
        # Slides whose section is unchecked go to the skip set
        for i, sec in enumerate(deck_sections):
            if not section_selected[i]:
                skip_slide_numbers.update(sec["slide_numbers"])
        st.markdown("")

    o1, o2 = st.columns(2)
    with o1:
        analyze_all = st.checkbox(
            "Evaluar todos los slides (sin skip por role)",
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
        or s["slide_number"] in skip_slide_numbers
    )
    will_visual = (
        sum(
            1 for s in deck_to_run["slides"]
            if s.get("has_visuals") and s["slide_number"] not in skip_slide_numbers
        )
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
            skip_slide_numbers=skip_slide_numbers or None,
            visual_analysis=visual_enabled,
            images_by_slide=images_by_slide or {},
        )
    )

    st.markdown("---")
    getattr(styles, "scroll_anchor", lambda *a, **kw: None)("qa-progress")
    styles.section_label("Progreso")
    progress_bar = st.empty()
    live_table = st.empty()
    error_box = st.empty()

    # Bring the progress section into view as soon as the run starts.
    getattr(styles, "auto_scroll_to", lambda *a, **kw: None)("qa-progress")

    completed_slides: list[dict] = []
    result_obj = None
    error = None
    current_phase: str = "Iniciando…"
    estimated_total = deck_to_run["slide_count"]
    run_start_ts = __import__("time").monotonic()

    def _current_sev_counts() -> dict[str, int]:
        counts = {s: 0 for s in SEVERITY_ORDER}
        for entry in completed_slides:
            f = entry["finding"]
            sev = f.get("severity") or severity_for(f.get("score"))
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    def _render_progress(
        payload: dict | None = None,
        *,
        current_label: str | None = None,
        indeterminate: bool = False,
    ):
        if payload:
            completed = payload["completed"]
            total = payload["total"]
        else:
            completed = len(completed_slides)
            total = estimated_total if estimated_total > 0 else max(1, len(completed_slides))
        elapsed = __import__("time").monotonic() - run_start_ts
        progress_bar.markdown(
            getattr(styles, "live_progress_html", lambda *a, **kw: "")(
                completed, total,
                sev_counts=_current_sev_counts(),
                elapsed_s=elapsed,
                current_label=current_label,
                phase=current_phase,
                indeterminate=indeterminate,
            ),
            unsafe_allow_html=True,
        )

    # Initial render: show the dashboard immediately, indeterminate state.
    _render_progress(indeterminate=True)

    def _render_live_table():
        if not completed_slides:
            return
        rows = []
        for entry in completed_slides:
            f = entry["finding"]
            title = (f.get("action_title") or {}).get("current_title") or ""
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
            current_phase = payload
            # While no slides have been completed yet, keep the bar
            # indeterminate so the user sees motion during the setup phases.
            _render_progress(indeterminate=(len(completed_slides) == 0))
        elif kind == "slide_done":
            completed_slides.append(payload)
            n = payload["slide_number"]
            title = (payload.get("finding") or {}).get("action_title", {}).get("current_title") or ""
            label = f"{n} · {title[:50]}" + ("…" if len(title) > 50 else "") if title else str(n)
            _render_progress(payload, current_label=label)
            _render_live_table()
        elif kind == "visual_done":
            current_phase = f"Visión · {payload['completed']} / {payload['total']}"
            _render_progress()
        elif kind == "error":
            error = payload
            break
        elif kind == "result":
            result_obj = payload

    if error:
        error_box.error(f"Error · {error}")
        st.stop()
    if result_obj is None:
        error_box.error("No se recibió resultado.")
        st.stop()

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
    # No results yet → ensure the floating navigator isn't lingering from a
    # previous file's session.
    getattr(styles, "hide_nav", lambda: None)()
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


# Top metrics
st.markdown("---")
getattr(styles, "scroll_anchor", lambda *a, **kw: None)("qa-results")
provider_raw = result.get("provider", "")
provider_label = PROVIDER_LABELS.get(provider_raw, provider_raw)
mode_label = "Modo local" if result["mode"] == "local" else f"{provider_label} · modo full"
skipped_count = len(overview.get("skipped_slides", []))
meta_bits = [mode_label, f"{total} slides"]
if skipped_count:
    meta_bits.append(f"{skipped_count} skipped")

# Bring the results into view once per file/run
_results_marker = f"{file_hash}__{result.get('mode', '')}"
if st.session_state.get("_scrolled_to_results") != _results_marker:
    st.session_state["_scrolled_to_results"] = _results_marker
    getattr(styles, "auto_scroll_to", lambda *a, **kw: None)("qa-results")

st.markdown(f"## {file_name}")
st.caption("  ·  ".join(meta_bits))

# Cost card content
if "actual_cost" in result:
    cost_value = f"${result['actual_cost']['total_usd']:.3f}"
    cost_sub = "real"
else:
    cost_value = "$0"
    cost_sub = "local · sin API"

styles.summary_cards([
    {
        "label": "Score promedio",
        "value": f"{avg_score:.1f}",
        "denom": "/10",
        "sub": f"{sev_counts['ok']} OK · {total} slides",
        "variant": "score",
    },
    {
        "label": "Critical",
        "value": str(sev_counts["critical"]),
        "sub": "slides bloqueantes" if sev_counts["critical"] else "ninguno",
        "variant": "sev-critical",
        "empty": sev_counts["critical"] == 0,
    },
    {
        "label": "Warning",
        "value": str(sev_counts["warning"]),
        "sub": "issues a revisar" if sev_counts["warning"] else "ninguno",
        "variant": "sev-warning",
        "empty": sev_counts["warning"] == 0,
    },
    {
        "label": "Nit",
        "value": str(sev_counts["nit"]),
        "sub": "mejoras menores" if sev_counts["nit"] else "ninguno",
        "variant": "sev-nit",
        "empty": sev_counts["nit"] == 0,
    },
    {
        "label": "Costo",
        "value": cost_value,
        "sub": cost_sub,
        "variant": "cost",
    },
])


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


# ───────── Análisis general del deck (promoted from expander) ─────────
styles.overview_panel(overview, sev_counts, total)

# Sentinel that drives navigator visibility. Placed right after the overview
# so the navigator appears the moment the user scrolls past it, and hides
# again when they scroll back up to it.
getattr(styles, "scroll_anchor", lambda *a, **kw: None)("qa-nav-trigger", top_margin_px=0)
getattr(styles, "nav_visibility_observer", lambda *a, **kw: None)("qa-nav-trigger")


# ───────── Filtros ─────────
styles.section_label("Filtrar por severidad")
fcols = st.columns(4)
show_sev: dict[str, bool] = {}
for i, sev in enumerate(SEVERITY_ORDER):
    with fcols[i]:
        label = f"{SEVERITY_EMOJI[sev]} {SEVERITY_LABELS[sev]} ({sev_counts[sev]})"
        show_sev[sev] = st.checkbox(label, value=True, key=f"sev_{sev}")

hide_skipped = st.checkbox("Ocultar skipped", value=False)


# ───────── Slide cards filtered + grouped by section ─────────
visible = [
    s for s in slides
    if show_sev.get(s.get("severity") or severity_for(s.get("score")), False)
    and (not hide_skipped or not s.get("_skipped"))
]
st.caption(f"Mostrando {len(visible)} de {total} slides")
st.markdown("")

# Re-detect sections from the result's deck snapshot (sections are inherent to the input deck)
result_sections = detect_sections({"slides": slides})

# Slide navigator (sticky timeline with thumbnails)
# Shows ALL slides so the user can always jump to any of them; slides hidden by
# the current filter set are dimmed but still clickable. Zoom control lives
# inside the sticky panel (pure HTML radios + CSS, no Streamlit rerun).
if slides:
    visible_nums = {s["slide_number"] for s in visible}
    styles.slide_navigator(
        slides,
        sections=result_sections,
        thumbs=thumbs,
        visible_slide_numbers=visible_nums,
    )

if result_sections:
    visible_by_n = {s["slide_number"]: s for s in visible}
    for sec in result_sections:
        sec_slides = [visible_by_n[n] for n in sec["slide_numbers"] if n in visible_by_n]
        if not sec_slides:
            continue
        styles.section_divider(sec, total)
        for slide in sec_slides:
            thumb_bytes = thumbs.get(slide["slide_number"]) if thumbs else None
            st.markdown(
                styles.slide_card_html(slide, thumb_bytes=thumb_bytes),
                unsafe_allow_html=True,
            )
else:
    for slide in visible:
        thumb_bytes = thumbs.get(slide["slide_number"]) if thumbs else None
        st.markdown(
            styles.slide_card_html(slide, thumb_bytes=thumb_bytes),
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Visual analysis summary — shows ONLY non-redundant info: count + a quick
# index of slides flagged. Detailed notes / suggestions live inline in each
# slide card above; repeating them here adds noise.
# ---------------------------------------------------------------------------

if overview.get("visual_analysis_enabled"):
    visual_slides_data = [s for s in slides if s.get("visual")]
    if visual_slides_data:
        flagged = [
            s for s in visual_slides_data
            if not (s["visual"].get("visual_quality") or {}).get("ok", True)
        ]
        ok_count = len(visual_slides_data) - len(flagged)
        if flagged:
            links = " · ".join(
                f'<a href="#qa-slide-{s["slide_number"]}" '
                'style="color: var(--accent); text-decoration: none; font-weight: 700;">'
                f'#{s["slide_number"]}</a>'
                for s in flagged
            )
            summary = (
                f'<strong>{len(flagged)}</strong> slide(s) con issues visuales · '
                f'<strong>{ok_count}</strong> OK · Ver detalle inline en cada card: {links}'
            )
        else:
            summary = (
                f'<strong>{len(visual_slides_data)}</strong> slide(s) con imágenes '
                'analizadas · todas OK.'
            )
        st.markdown(
            '<div style="margin: 0.4rem 0 1rem 0; padding: 12px 16px; '
            'background: var(--surface-2); border: 1px solid var(--border-soft); '
            'border-radius: 10px; font-size: 0.88rem; color: var(--text);">'
            '<span style="font-size: 0.66rem; text-transform: uppercase; '
            'letter-spacing: 0.10em; font-weight: 700; color: var(--text-muted); '
            'display: block; margin-bottom: 6px;">Análisis visual · resumen</span>'
            f'{summary}'
            '</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Acciones Holmes — descargar review anotado · aplicar fixes · comparar versiones
# ---------------------------------------------------------------------------

from exporter import (  # noqa: E402  (deferred import — runs only after analysis)
    apply_quick_fixes,
    available_fixes_for_slide,
    export_annotated_pptx,
)
from comparator import compare_results  # noqa: E402

st.markdown("---")
styles.section_label("Acciones Holmes")

_pptx_bytes_cached = st.session_state.get(f"pptx_bytes__{file_hash}")


def _write_temp_pptx(b: bytes) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as t:
        t.write(b)
        return Path(t.name)


_action_tabs = st.tabs([
    "📥 Descargar review",
    "🛠️ Aplicar fixes",
    "🔁 Comparar versiones",
])

# ----- 1) Descargar review anotado -----
with _action_tabs[0]:
    st.markdown(
        "Holmes inyecta sus findings en las **speaker notes** de cada slide "
        "(sin tocar el contenido visual) y agrega un slide final con el "
        "resumen del deck. Abrí el archivo en PowerPoint para ver el review "
        "inline."
    )
    if not _pptx_bytes_cached:
        st.warning("No tengo los bytes del deck cacheados — subí el archivo de nuevo.")
    else:
        if st.button("Generar review anotado", type="primary"):
            with st.spinner("Anotando deck…"):
                src_path = _write_temp_pptx(_pptx_bytes_cached)
                try:
                    annotated_bytes = export_annotated_pptx(str(src_path), result)
                finally:
                    try: src_path.unlink()
                    except OSError: pass
            out_name = (
                st.session_state.get(f"pptx_filename__{file_hash}", file_name)
                .replace(".pptx", "")
                + "_Holmes_review.pptx"
            )
            st.success(f"Review listo · {len(annotated_bytes) // 1024} KB")
            st.download_button(
                "⬇️ Descargar .pptx anotado",
                data=annotated_bytes,
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )

# ----- 2) Aplicar fixes -----
with _action_tabs[1]:
    # Collect available fixes from every slide finding
    all_fixes: list[dict] = []
    for s in slides:
        all_fixes.extend(available_fixes_for_slide(s))

    if not all_fixes:
        st.info("Holmes no identificó fixes auto-aplicables en este deck. "
                "Las sugerencias de redacción más complejas siguen requiriendo "
                "edición manual.")
    elif not _pptx_bytes_cached:
        st.warning("No tengo los bytes del deck cacheados — subí el archivo de nuevo.")
    else:
        st.markdown(
            f"**{len(all_fixes)}** fixes auto-aplicables disponibles. "
            "Seleccioná los que querés que Holmes aplique y descargá el "
            "deck modificado."
        )
        # Group by slide for cleaner display
        fixes_by_slide: dict[int, list[dict]] = {}
        for f in all_fixes:
            fixes_by_slide.setdefault(f["slide_number"], []).append(f)

        selected_keys: set[str] = set()
        for n in sorted(fixes_by_slide.keys()):
            with st.expander(f"Slide {n} · {len(fixes_by_slide[n])} fix(es)"):
                for f in fixes_by_slide[n]:
                    key = f"fix__{file_hash}__{n}__{f['id']}"
                    checked = st.checkbox(
                        f["label"], value=True, key=key,
                    )
                    st.caption(f"Antes:  {f['preview_before'][:120]}")
                    st.caption(f"Después: {f['preview_after'][:120]}")
                    if checked:
                        selected_keys.add(key)

        # Re-collect selected fix objects
        to_apply: list[dict] = []
        for n, fix_list in fixes_by_slide.items():
            for f in fix_list:
                key = f"fix__{file_hash}__{n}__{f['id']}"
                if key in selected_keys:
                    to_apply.append(f)

        st.markdown("")
        if st.button(
            f"Aplicar {len(to_apply)} fix(es) y descargar",
            type="primary",
            disabled=(len(to_apply) == 0),
        ):
            with st.spinner("Aplicando fixes…"):
                src_path = _write_temp_pptx(_pptx_bytes_cached)
                try:
                    fixed_bytes, report = apply_quick_fixes(
                        str(src_path), result, to_apply,
                    )
                finally:
                    try: src_path.unlink()
                    except OSError: pass
            out_name = (
                st.session_state.get(f"pptx_filename__{file_hash}", file_name)
                .replace(".pptx", "")
                + "_Holmes_fixed.pptx"
            )
            counts = report["counts"]
            if counts["failed"]:
                st.warning(
                    f"{counts['applied']}/{counts['total_requested']} aplicados · "
                    f"{counts['failed']} fallaron."
                )
                for f in report["failed"][:10]:
                    st.caption(f"Slide {f['slide_number']} · {f['id']} · {f['reason']}")
            else:
                st.success(f"{counts['applied']} fixes aplicados.")
            st.download_button(
                "⬇️ Descargar .pptx con fixes aplicados",
                data=fixed_bytes,
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )

# ----- 3) Comparar versiones -----
with _action_tabs[2]:
    st.markdown(
        "Subí una **versión posterior** del deck (después de aplicar feedback) "
        "y Holmes te muestra qué slides mejoraron, cuáles regresionaron y el "
        "cambio en el score promedio."
    )
    v2_upload = st.file_uploader(
        "Versión 2 del deck", type=["pptx"], key="v2_uploader",
        label_visibility="collapsed",
    )

    if v2_upload is not None:
        v2_bytes = v2_upload.getvalue()
        v2_hash = hashlib.sha1(v2_bytes).hexdigest()[:16]

        # Cache the v2 result so we don't re-analyze on every rerun
        v2_cache_key = f"qa_result_v2__{v2_hash}"
        if v2_cache_key in st.session_state:
            v2_result = st.session_state[v2_cache_key]
        else:
            with st.spinner("Analizando versión 2 (modo local)…"):
                tmp_v2 = _write_temp_pptx(v2_bytes)
                try:
                    deck_v2 = extract_deck(tmp_v2)
                finally:
                    try: tmp_v2.unlink()
                    except OSError: pass
                v2_result = None
                for kind, payload in run_local_qa(v2_upload.name, deck_v2):
                    if kind == "result":
                        v2_result = payload
                if v2_result is None:
                    st.error("No se pudo analizar la versión 2.")
                    st.stop()
                st.session_state[v2_cache_key] = v2_result

        diff = compare_results(result, v2_result)
        agg = diff["aggregate"]
        delta = agg["score_delta"]
        delta_str = f"{delta:+.1f}"
        sign_color = "#2dba8a" if delta > 0 else "#e94e77" if delta < 0 else "var(--text-muted)"

        st.markdown(
            f'<div style="display:flex;gap:24px;align-items:baseline;margin:14px 0 18px 0;">'
            f'<div><span style="font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.10em;color:var(--text-muted);font-weight:700">Score promedio</span><br>'
            f'<span style="font-size:1.8rem;font-weight:800;">{agg["score_v1"]:.1f}</span>'
            f'<span style="color:var(--text-muted);"> → </span>'
            f'<span style="font-size:1.8rem;font-weight:800;">{agg["score_v2"]:.1f}</span>'
            f' <span style="color:{sign_color};font-weight:700;margin-left:8px;">{delta_str}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("✓ Mejoraron", len(diff["improved"]))
        c2.metric("✗ Regresionaron", len(diff["regressed"]))
        c3.metric("Sin cambio", len(diff["unchanged"]))

        if diff["improved"]:
            with st.expander(f"Mejoraron ({len(diff['improved'])})", expanded=True):
                for row in diff["improved"][:25]:
                    st.markdown(
                        f"**{row['label']}** · {row['severity_v1']} → {row['severity_v2']} "
                        f"· score {row['score_v1']}→{row['score_v2']}"
                    )
        if diff["regressed"]:
            with st.expander(f"Regresionaron ({len(diff['regressed'])})", expanded=True):
                for row in diff["regressed"][:25]:
                    st.markdown(
                        f"**{row['label']}** · {row['severity_v1']} → {row['severity_v2']} "
                        f"· score {row['score_v1']}→{row['score_v2']}"
                    )
        if diff["added"] or diff["removed"]:
            with st.expander(f"Estructura del deck ({len(diff['added'])} agregados · {len(diff['removed'])} eliminados)"):
                for row in diff["added"]:
                    st.markdown(f"➕ **{row['label']}** · {row['severity_v2']}")
                for row in diff["removed"]:
                    st.markdown(f"➖ **{row['label']}**")


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
