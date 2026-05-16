"""Streamlit design system — Recreo-inspired.

Single entry point: `inject()` — call once near the top of app.py.

CSS philosophy:
- NEVER use `*` selectors or override `font-family` globally — that breaks
  Material Symbols / icon fonts used by Streamlit's built-in components.
- Target specific Streamlit `data-testid` attributes and known classes.
- Inherit-don't-force: let Streamlit's defaults work, just retint.
"""

from __future__ import annotations

import streamlit as st


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  --bg-base: #f4f1ec;
  --bg-panel: #3d0d1a;
  --bg-panel-grad-1: #3d0d1a;
  --bg-panel-grad-2: #5c1428;
  --bg-card: #ffffff;
  --surface-2: #faf6f1;
  --surface-3: #f0ebe4;

  --accent: #e94e77;
  --accent-hover: #d13d64;
  --accent-soft: rgba(233, 78, 119, 0.10);
  --accent-glow: rgba(233, 78, 119, 0.18);

  --text-primary: #2d0e17;
  --text-muted: rgba(61, 13, 26, 0.58);
  --text-faint: rgba(61, 13, 26, 0.38);

  --status-ok: #047857;
  --status-ok-bg: #ecfdf4;
  --status-warn: #b45309;
  --status-warn-bg: #fef6e3;
  --status-crit: #b91c1c;
  --status-crit-bg: #fef0f0;
  --status-info: #6d28d9;
  --status-info-bg: #f3eefe;

  --border: rgba(61,13,26,0.10);
  --border-soft: rgba(61,13,26,0.06);
  --border-strong: rgba(61,13,26,0.18);

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius: 14px;
  --radius-lg: 20px;

  --ease-spring: cubic-bezier(0.32, 0.72, 0, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-quart: cubic-bezier(0.22, 1, 0.36, 1);

  --dur-micro: 140ms;
  --dur-normal: 220ms;

  --shadow-sm: 0 1px 3px rgba(61,13,26,0.04), 0 2px 6px rgba(61,13,26,0.03);
  --shadow-md: 0 4px 12px rgba(61,13,26,0.06), 0 8px 24px rgba(61,13,26,0.04);
  --shadow-lg: 0 20px 48px rgba(61,13,26,0.14);
}

/* ──────────────────────────────────────────────
   Body background — cream with subtle gradient
   ────────────────────────────────────────────── */
.stApp {
  background: var(--bg-base);
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(233,78,119,0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(61,13,26,0.04) 0%, transparent 50%);
  background-attachment: fixed;
}

/* ──────────────────────────────────────────────
   Typography — target body/heading containers
   only. NEVER use `*` here, it breaks icons.
   ────────────────────────────────────────────── */
section[data-testid="stMain"] [data-testid="stMarkdownContainer"],
section[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stMain"] [data-testid="stMarkdownContainer"] li,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  color: var(--text-primary);
  letter-spacing: -0.005em;
  line-height: 1.55;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text-primary) !important;
  letter-spacing: -0.022em;
  font-weight: 800;
}
[data-testid="stMarkdownContainer"] h1 {
  font-size: 2rem;
  line-height: 1.1;
  margin-top: 0.4rem;
}
[data-testid="stMarkdownContainer"] h2 {
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.2;
}
[data-testid="stMarkdownContainer"] h3 {
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.25;
}

/* Caption styling */
[data-testid="stCaptionContainer"] p,
small {
  color: var(--text-muted) !important;
  font-size: 0.82rem;
  font-weight: 500;
}

/* ──────────────────────────────────────────────
   Sidebar — light cream surface with stripe
   ────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f7f4ef 0%, #f0ebe4 100%);
  border-right: 1px solid var(--border);
}

/* ──────────────────────────────────────────────
   Buttons — burgundy default, pink primary hover
   ────────────────────────────────────────────── */
.stButton > button {
  border-radius: var(--radius-sm);
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 600;
  font-size: 0.88rem;
  padding: 10px 18px;
  border: 1.5px solid var(--border-strong);
  background: transparent;
  color: var(--bg-panel);
  transition:
    transform var(--dur-micro) var(--ease-out-quart),
    background var(--dur-normal) var(--ease-spring),
    border-color var(--dur-normal) var(--ease-spring),
    color var(--dur-normal) var(--ease-spring),
    box-shadow var(--dur-normal) var(--ease-spring);
}
.stButton > button:hover {
  background: var(--bg-panel);
  border-color: var(--bg-panel);
  color: white;
  transform: translateY(-1px);
}
.stButton > button:active {
  transform: translateY(0) scale(0.98);
  transition-duration: 90ms;
}

/* Primary button = burgundy → pink hover */
.stButton > button[kind="primary"] {
  background: var(--bg-panel) !important;
  color: white !important;
  border-color: var(--bg-panel) !important;
  box-shadow: 0 4px 12px rgba(61,13,26,0.18);
}
.stButton > button[kind="primary"]:hover {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  box-shadow: 0 8px 20px rgba(233,78,119,0.30);
}

/* CRITICAL: text inside ANY button must inherit color from the button,
   not from the global markdown-container color rule. Streamlit nests
   button labels inside a [data-testid="stMarkdownContainer"] > p, and
   our global rule above turned those black on the burgundy primary. */
.stButton > button p,
.stButton > button [data-testid="stMarkdownContainer"],
.stButton > button [data-testid="stMarkdownContainer"] p,
.stDownloadButton > button p,
.stDownloadButton > button [data-testid="stMarkdownContainer"],
.stDownloadButton > button [data-testid="stMarkdownContainer"] p {
  color: inherit !important;
  font-family: inherit !important;
  font-weight: inherit !important;
  font-size: inherit !important;
  margin: 0 !important;
}

/* Download buttons */
.stDownloadButton > button {
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border-strong);
  font-weight: 600;
  background: white;
  color: var(--bg-panel);
}
.stDownloadButton > button:hover {
  background: var(--bg-panel);
  color: white;
  border-color: var(--bg-panel);
}

/* ──────────────────────────────────────────────
   Metric cards — compact, not gigantic
   ────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.75);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 12px 16px;
  box-shadow: var(--shadow-sm);
  transition: var(--dur-normal) var(--ease-spring);
}
[data-testid="stMetric"]:hover {
  border-color: var(--border);
  box-shadow: var(--shadow-md);
}
[data-testid="stMetricLabel"] {
  color: var(--text-muted) !important;
}
[data-testid="stMetricLabel"] p {
  color: var(--text-muted) !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.015em;
  line-height: 1.2;
}
[data-testid="stMetricDelta"] {
  font-weight: 600 !important;
  font-size: 0.78rem !important;
}

/* ──────────────────────────────────────────────
   Bordered containers
   ────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: var(--radius);
  border: 1px solid var(--border-soft);
  background: rgba(255,255,255,0.65);
  transition: var(--dur-normal) var(--ease-spring);
}

/* ──────────────────────────────────────────────
   Tabs — pink underline indicator
   ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  color: var(--text-muted) !important;
  font-weight: 600;
  padding: 12px 18px;
  border-radius: 0;
}
.stTabs [data-baseweb="tab"] p {
  color: var(--text-muted) !important;
  font-weight: 600 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] p {
  color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
  background: var(--accent) !important;
  height: 2.5px !important;
  border-radius: 2px;
}

/* ──────────────────────────────────────────────
   Expander — preserve native chevron icon
   ────────────────────────────────────────────── */
[data-testid="stExpander"] {
  border: 1px solid var(--border-soft) !important;
  border-radius: var(--radius-md) !important;
  background: rgba(255,255,255,0.55);
  margin-bottom: 8px;
}
[data-testid="stExpander"] summary {
  font-weight: 600;
  color: var(--text-primary);
}
/* DON'T touch SVG/icon inside expander */

/* ──────────────────────────────────────────────
   Inputs / radios / selects / sliders
   ────────────────────────────────────────────── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: white;
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 500;
}
.stTextInput input:focus,
.stNumberInput input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

/* File uploader — generous, inviting */
[data-testid="stFileUploader"] section {
  background: rgba(255,255,255,0.6);
  border: 2px dashed var(--border-strong);
  border-radius: var(--radius);
  padding: 24px;
  transition: var(--dur-normal) var(--ease-spring);
}
[data-testid="stFileUploader"] section:hover {
  border-color: var(--accent);
  background: rgba(255,255,255,0.85);
}

/* Radio: accent active state */
.stRadio label {
  font-weight: 500;
}
.stRadio [role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] > div:first-child {
  border-color: var(--accent) !important;
  background: var(--accent) !important;
}

/* Slider track */
[data-testid="stSlider"] [role="slider"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* Checkbox: accent when checked */
.stCheckbox [data-baseweb="checkbox"] [aria-checked="true"] {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* ──────────────────────────────────────────────
   Progress bar — accent gradient
   ────────────────────────────────────────────── */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--bg-panel) 0%, var(--accent) 100%);
  border-radius: 100px;
}

/* ──────────────────────────────────────────────
   Alerts (info, success, warning, error)
   ────────────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  font-weight: 500;
  padding: 12px 16px;
}

/* ──────────────────────────────────────────────
   Dataframe
   ────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border-radius: var(--radius-md);
  border: 1px solid var(--border-soft);
  overflow: hidden;
}

/* ──────────────────────────────────────────────
   Inline `code`
   ────────────────────────────────────────────── */
[data-testid="stMarkdownContainer"] code {
  background: var(--accent-soft);
  color: var(--bg-panel);
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.82em;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
}

/* ──────────────────────────────────────────────
   Markdown blockquote + hr
   ────────────────────────────────────────────── */
[data-testid="stMarkdownContainer"] blockquote {
  border-left: 3px solid var(--accent);
  padding-left: 14px;
  color: var(--text-muted);
  font-style: italic;
  margin-left: 0;
}
hr {
  border: none;
  border-top: 1px solid var(--border-soft);
  margin: 1.4rem 0;
}

/* ──────────────────────────────────────────────
   Custom utility classes
   ────────────────────────────────────────────── */
.qa-eyebrow {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

.qa-section-label {
  display: block;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.qa-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid;
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
.qa-pill.ok    { background: var(--status-ok-bg);   color: var(--status-ok);   border-color: rgba(4,120,87,0.18); }
.qa-pill.warn  { background: var(--status-warn-bg); color: var(--status-warn); border-color: rgba(180,83,9,0.22); }
.qa-pill.crit  { background: var(--status-crit-bg); color: var(--status-crit); border-color: rgba(185,28,28,0.22); }
.qa-pill.info  { background: var(--status-info-bg); color: var(--status-info); border-color: rgba(109,40,217,0.18); }
.qa-pill.nit   { background: #eef6fc;               color: #075985;            border-color: rgba(7,89,133,0.18); }
.qa-pill.muted { background: rgba(61,13,26,0.04);   color: var(--text-muted);  border-color: var(--border-soft); }

/* Severity-specific pills (used for slide severity bands) */
.qa-pill.sev-critical { background: var(--status-crit-bg); color: var(--status-crit); border-color: rgba(185,28,28,0.22); }
.qa-pill.sev-warning  { background: var(--status-warn-bg); color: var(--status-warn); border-color: rgba(180,83,9,0.22); }
.qa-pill.sev-nit      { background: #eef6fc;               color: #075985;            border-color: rgba(7,89,133,0.18); }
.qa-pill.sev-ok       { background: var(--status-ok-bg);   color: var(--status-ok);   border-color: rgba(4,120,87,0.18); }

.qa-cost-panel {
  background: linear-gradient(170deg, #3d0d1a 0%, #5c1428 60%, #3d0d1a 100%);
  color: white;
  border-radius: var(--radius);
  padding: 18px 22px;
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
  margin-bottom: 0.5rem;
}
.qa-cost-panel::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 100px;
  background: radial-gradient(ellipse at 50% -20%, rgba(233,78,119,0.30) 0%, transparent 70%);
  pointer-events: none;
}
.qa-cost-panel-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255,255,255,0.65);
  font-weight: 600;
  margin-bottom: 4px;
}
.qa-cost-panel-value {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: white;
  line-height: 1.1;
}
.qa-cost-panel-sub {
  margin-top: 4px;
  font-size: 0.78rem;
  color: rgba(255,255,255,0.7);
  font-weight: 500;
}
.qa-cost-panel-accent { color: var(--accent); }

/* ──────────────────────────────────────────────
   Check block — used in per-slide cards
   ────────────────────────────────────────────── */
.qa-check {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.6);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-md);
  margin-bottom: 10px;
  transition: var(--dur-normal) var(--ease-spring);
}
.qa-check:hover {
  border-color: var(--border);
  background: rgba(255,255,255,0.85);
}
.qa-check-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.qa-check-title {
  font-weight: 700;
  font-size: 0.92rem;
  color: var(--text-primary);
  font-family: 'Inter', system-ui, sans-serif;
}
.qa-check-current {
  display: block;
  padding: 6px 10px;
  background: var(--surface-3);
  border-left: 3px solid var(--border-strong);
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-size: 0.82rem;
  color: var(--text-primary);
  margin: 4px 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.qa-check-notes {
  font-size: 0.85rem;
  color: var(--text-primary);
  line-height: 1.45;
}
.qa-check-suggestion {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  background: var(--accent-soft);
  border-left: 3px solid var(--accent);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--bg-panel);
  line-height: 1.45;
  margin-top: 4px;
}
.qa-check-suggestion::before {
  content: "→";
  color: var(--accent);
  font-weight: 700;
  flex-shrink: 0;
}
.qa-check-suggestion strong {
  color: var(--bg-panel);
  font-weight: 700;
}

/* Hide Streamlit chrome */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
"""


def inject() -> None:
    """Inject design tokens + component overrides. Call once at app start."""
    st.markdown(CSS, unsafe_allow_html=True)


def eyebrow(text: str) -> None:
    """Small uppercase accent text above a section heading."""
    st.markdown(f'<span class="qa-eyebrow">{text}</span>', unsafe_allow_html=True)


def section_label(text: str) -> None:
    """Section divider label — uppercase, muted."""
    st.markdown(f'<span class="qa-section-label">{text}</span>', unsafe_allow_html=True)


def pill(text: str, variant: str = "muted") -> str:
    """Inline status pill. Variants: ok | warn | crit | info | muted."""
    return f'<span class="qa-pill {variant}">{text}</span>'


def cost_panel(label: str, value: str, sub: str | None = None) -> None:
    """Burgundy panel for highlighted cost displays.

    NOTE: HTML must NOT have leading whitespace — markdown treats lines
    indented 4+ spaces as a code block, so the divs would render literally.
    """
    sub_html = f'<div class="qa-cost-panel-sub">{sub}</div>' if sub else ""
    html = (
        '<div class="qa-cost-panel">'
        f'<div class="qa-cost-panel-label">{label}</div>'
        f'<div class="qa-cost-panel-value">{value}</div>'
        f'{sub_html}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _escape_html(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def check_block(
    title: str,
    pill_text: str,
    pill_variant: str,
    *,
    current_value: str | None = None,
    notes: str | None = None,
    suggestion: str | None = None,
) -> None:
    """Render one check as a self-contained card.

    NOTE: do NOT indent the HTML — leading whitespace (4+ spaces) makes
    Streamlit's markdown parser treat it as a code block, so the divs
    render as literal text instead of styled HTML.
    """
    current_html = (
        f'<div class="qa-check-current">{_escape_html(current_value)}</div>'
        if current_value
        else ""
    )
    notes_html = (
        f'<div class="qa-check-notes">{_escape_html(notes)}</div>' if notes else ""
    )
    suggestion_html = (
        f'<div class="qa-check-suggestion"><div>{_escape_html(suggestion)}</div></div>'
        if suggestion
        else ""
    )
    html = (
        '<div class="qa-check">'
        '<div class="qa-check-header">'
        f'<span class="qa-check-title">{_escape_html(title)}</span>'
        f'<span class="qa-pill {pill_variant}">{_escape_html(pill_text)}</span>'
        '</div>'
        f'{current_html}'
        f'{notes_html}'
        f'{suggestion_html}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
