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

/* Tighten Streamlit's default top padding so the hero starts close to the top. */
[data-testid="stMainBlockContainer"],
.stMainBlockContainer {
  padding-top: 1.5rem !important;
  padding-bottom: 2rem !important;
}
@media (max-width: 720px) {
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer { padding-top: 1rem !important; }
}

/* Tighten the vertical rhythm between top-level Streamlit elements.
   Streamlit's default gap inside vertical blocks is ~1rem — too generous
   for our dense layout. Pull it in by ~40%. */
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {
  gap: 0.55rem !important;
}

/* Hide Streamlit's default top header/toolbar (hamburger menu, "Made with
   Streamlit" status, etc.) — for end-user-facing branding we don't want
   those affordances. */
[data-testid="stHeader"],
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
}
/* Reclaim the space the hidden header would have occupied. */
.stApp { padding-top: 0 !important; }

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
   Metric cards — richer styling with subtle gradient + accent corner
   ────────────────────────────────────────────── */
[data-testid="stMetric"] {
  position: relative;
  background:
    radial-gradient(ellipse 60% 80% at 100% 0%, rgba(233,78,119,0.06) 0%, transparent 60%),
    linear-gradient(178deg, #ffffff 0%, var(--surface-2) 100%);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 12px 18px 14px;
  box-shadow: 0 1px 2px rgba(61,13,26,0.04), 0 3px 8px rgba(61,13,26,0.04);
  transition: transform 180ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 180ms ease, border-color 180ms ease;
  overflow: hidden;
}
[data-testid="stMetric"]::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--accent) 0%, #c43b62 100%);
  opacity: 0.85;
}
[data-testid="stMetric"]:hover {
  transform: translateY(-1px);
  border-color: rgba(233,78,119,0.24);
  box-shadow: 0 2px 4px rgba(61,13,26,0.05), 0 8px 20px rgba(61,13,26,0.08);
}
[data-testid="stMetricLabel"] {
  color: var(--text-muted) !important;
}
[data-testid="stMetricLabel"] p {
  color: var(--text-muted) !important;
  font-size: 0.66rem !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  margin-bottom: 2px !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.65rem !important;
  font-weight: 800 !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.028em;
  line-height: 1.05;
  font-feature-settings: "tnum" 1, "lnum" 1;
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
   Tabs — top nav bar styled as a segmented pill control
   ────────────────────────────────────────────── */
.stTabs {
  margin: 0 0 1.6rem 0;
}
.stTabs [data-baseweb="tab-list"] {
  gap: 4px !important;
  border: 1px solid var(--border-soft) !important;
  border-bottom: 1px solid var(--border-soft) !important;
  padding: 5px !important;
  background: linear-gradient(180deg, var(--surface-2) 0%, #f2ece6 100%);
  border-radius: 100px !important;
  display: inline-flex !important;
  box-shadow: 0 1px 2px rgba(61,13,26,0.04), 0 4px 14px rgba(61,13,26,0.05);
  width: auto !important;
  min-width: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  font-weight: 600 !important;
  padding: 8px 20px !important;
  border-radius: 100px !important;
  transition: background 180ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              color 180ms ease, transform 100ms ease !important;
  min-height: auto !important;
  height: auto !important;
  border: 1px solid transparent !important;
  letter-spacing: -0.005em;
  white-space: nowrap;
}
.stTabs [data-baseweb="tab"]:hover {
  background: rgba(233,78,119,0.08) !important;
  color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab"]:hover p {
  color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab"]:active {
  transform: scale(0.97);
}
.stTabs [data-baseweb="tab"] p {
  color: var(--text-muted) !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  margin: 0 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(180deg, var(--accent) 0%, #d13d64 100%) !important;
  box-shadow: 0 2px 8px rgba(233,78,119,0.35), 0 1px 0 rgba(255,255,255,0.4) inset;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] p {
  color: white !important;
  font-weight: 700 !important;
}
/* Remove the default underline / border-bottom — pill state replaces it */
.stTabs [data-baseweb="tab-highlight"] {
  display: none !important;
}
.stTabs [data-baseweb="tab-border"] {
  display: none !important;
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

/* File uploader — generous, inviting, with subtle gradient inside */
[data-testid="stFileUploader"] section {
  background:
    radial-gradient(ellipse 40% 60% at 50% 0%, rgba(233,78,119,0.05) 0%, transparent 70%),
    linear-gradient(180deg, #ffffff 0%, var(--surface-2) 100%);
  border: 2px dashed rgba(233,78,119,0.32);
  border-radius: 14px;
  padding: 18px 22px;
  transition: transform 180ms ease, border-color 180ms ease,
              box-shadow 180ms ease, background 180ms ease;
}
[data-testid="stFileUploader"] section:hover {
  border-color: var(--accent);
  background:
    radial-gradient(ellipse 50% 70% at 50% 0%, rgba(233,78,119,0.10) 0%, transparent 70%),
    linear-gradient(180deg, #ffffff 0%, #faf2ec 100%);
  box-shadow: 0 6px 20px rgba(233,78,119,0.12);
}
/* Uploaded file chip — match the burgundy palette */
[data-testid="stFileUploaderFile"] {
  background: white !important;
  border: 1px solid rgba(233,78,119,0.18) !important;
  border-radius: 10px !important;
  box-shadow: 0 1px 3px rgba(61,13,26,0.06);
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
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
  padding-bottom: 0;
}
.qa-section-label::before {
  content: "";
  width: 4px;
  height: 4px;
  border-radius: 100px;
  background: var(--accent);
  box-shadow: 0 0 6px rgba(233,78,119,0.55);
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
   Live progress dashboard (replaces st.progress during a run)
   ────────────────────────────────────────────── */
.qa-prog {
  background: var(--surface-2);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 18px 22px;
  margin: 0.6rem 0 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.qa-prog-head {
  display: flex;
  align-items: baseline;
  gap: 22px;
}
.qa-prog-pct {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--accent);
  line-height: 1;
  font-feature-settings: "tnum" 1, "lnum" 1;
  min-width: 100px;
}
.qa-prog-pct-sym {
  font-size: 1.4rem;
  font-weight: 600;
  margin-left: 2px;
  opacity: 0.6;
}
.qa-prog-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.qa-prog-fraction {
  font-size: 0.92rem;
  color: var(--text);
  letter-spacing: -0.005em;
}
.qa-prog-fraction strong {
  font-weight: 700;
  font-feature-settings: "tnum" 1, "lnum" 1;
}
.qa-prog-eta {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-weight: 500;
}
.qa-prog-current {
  font-size: 0.78rem;
  color: var(--accent);
  font-weight: 600;
  letter-spacing: -0.005em;
}
.qa-prog-bar-track {
  height: 8px;
  background: rgba(61,13,26,0.06);
  border-radius: 100px;
  overflow: hidden;
}
.qa-prog-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent) 0%, #c43b62 100%);
  border-radius: 100px;
  transition: width 320ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow: 0 0 12px rgba(233,78,119,0.45);
  position: relative;
  overflow: hidden;
}
/* Animated shimmer over the bar fill */
.qa-prog-bar-fill::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255,255,255,0.30) 50%,
    transparent 100%);
  animation: qa-prog-shimmer 1.4s linear infinite;
}
.qa-prog-bar-fill.done {
  background: linear-gradient(90deg, #2dba8a 0%, #1a8f66 100%);
  box-shadow: 0 0 12px rgba(45,186,138,0.45);
}
.qa-prog-bar-fill.done::after { animation: none; }

/* Indeterminate: sliding marquee bar */
.qa-prog-bar-fill.indeterminate {
  width: 35% !important;
  animation: qa-prog-indeterminate 1.4s cubic-bezier(0.65, 0.05, 0.36, 1) infinite;
  background: linear-gradient(90deg,
    transparent 0%, var(--accent) 30%, var(--accent) 70%, transparent 100%);
  box-shadow: none;
}
.qa-prog-bar-fill.indeterminate::after { display: none; }
@keyframes qa-prog-indeterminate {
  0%   { transform: translateX(-130%); }
  100% { transform: translateX(330%); }
}

@keyframes qa-prog-shimmer {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.qa-prog-phase {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.74rem;
  font-weight: 500;
  color: var(--text-muted);
  padding: 6px 12px;
  background: white;
  border: 1px solid var(--border-soft);
  border-radius: 100px;
  align-self: flex-start;
  letter-spacing: -0.005em;
}
.qa-prog-phase-dot {
  width: 6px;
  height: 6px;
  border-radius: 100px;
  background: var(--accent);
  box-shadow: 0 0 8px rgba(233,78,119,0.6);
  animation: qa-prog-phase-pulse 1.6s ease-in-out infinite;
}
@keyframes qa-prog-phase-pulse {
  0%, 100% { opacity: 0.5; }
  50%      { opacity: 1; }
}

/* ───── Holmes "investigando" scanner card ─────
   Prominent card with 3 synchronized vertically-cycling rolodexes (icon,
   name, description) so each tick reveals a rich check with context. A
   horizontal scan-line sweeps the card so it always looks alive, even
   though python-side audit progress isn't instrumented per-check (the
   checks run too fast — <200ms per slide — to wire telemetry to).

   The animation cadence is parameterized via the `--qa-scan-n` CSS
   variable set on `.qa-prog-scanner`, so changing the number of checks
   in the Python list automatically rescales the keyframes. Each check
   gets 1.6s of stage time. */

.qa-prog-scanner {
  --qa-scan-n: 14;
  --qa-scan-step: 1.6s;
  --qa-scan-duration: calc(var(--qa-scan-n) * var(--qa-scan-step));
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 18px;
  margin-top: 12px;
  background: linear-gradient(135deg,
    rgba(233, 78, 119, 0.04) 0%,
    rgba(244, 241, 236, 0.6) 100%);
  border: 1px solid rgba(233, 78, 119, 0.14);
  border-radius: 14px;
  overflow: hidden;
  isolation: isolate;
}

/* Horizontal scan-line sweeping left → right behind the content */
.qa-prog-scanner-sweep {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(233, 78, 119, 0.0) 30%,
    rgba(233, 78, 119, 0.12) 50%,
    rgba(233, 78, 119, 0.0) 70%,
    transparent 100%);
  transform: translateX(-100%);
  animation: qa-scan-sweep 2.6s cubic-bezier(0.45, 0, 0.55, 1) infinite;
  z-index: 0;
}
@keyframes qa-scan-sweep {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Header: eyebrow + radar + counter */
.qa-prog-scanner-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 1;
}
.qa-prog-scanner-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
}
.qa-prog-scanner-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* Pulsing radar dot */
.qa-scan-radar {
  position: relative;
  width: 8px;
  height: 8px;
  border-radius: 100px;
  background: var(--accent);
  flex-shrink: 0;
}
.qa-scan-radar::before,
.qa-scan-radar::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 100px;
  background: var(--accent);
  animation: qa-scan-radar 1.8s cubic-bezier(0.45, 0, 0.2, 1) infinite;
}
.qa-scan-radar::after { animation-delay: 0.9s; }
@keyframes qa-scan-radar {
  0%   { transform: scale(1); opacity: 0.7; }
  100% { transform: scale(3.5); opacity: 0; }
}

/* Body: large icon + (name + description) text stack */
.qa-prog-scanner-body {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

/* ── Icon rolodex ── */
.qa-scan-icon-wrap {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  background: white;
  border: 1px solid rgba(233, 78, 119, 0.18);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(233, 78, 119, 0.08),
              inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  position: relative;
}
.qa-scan-icon-roll {
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: qa-scan-icon-roll var(--qa-scan-duration)
             steps(var(--qa-scan-n)) infinite;
}
.qa-scan-icon-item {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  line-height: 1;
  /* Aa fallback for the casing check looks better in serif weight */
  font-weight: 700;
  color: var(--accent);
}
@keyframes qa-scan-icon-roll {
  from { transform: translateY(0); }
  to   { transform: translateY(calc(-52px * var(--qa-scan-n))); }
}

/* ── Text rolodexes (name + description in sync) ── */
.qa-scan-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.qa-scan-name-wrap,
.qa-scan-desc-wrap {
  height: 1.4em;
  overflow: hidden;
  position: relative;
  mask-image: linear-gradient(to bottom,
    transparent 0%, black 18%, black 82%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom,
    transparent 0%, black 18%, black 82%, transparent 100%);
}
.qa-scan-name-roll,
.qa-scan-desc-roll {
  display: flex;
  flex-direction: column;
  animation: qa-scan-text-roll var(--qa-scan-duration)
             cubic-bezier(0.7, 0, 0.3, 1) infinite;
}
/* The text rolodexes use eased transitions (not steps) so the swap looks
   like a smooth slide rather than a hard cut, while still landing on the
   same item the icon shows. The trick: hold each item ~70% of its slot
   then animate to the next. We approximate this with a many-stop
   percentage-keyed keyframe generated for n=14 here; if the list grows
   we adjust the timing. The icon rolodex stays on `steps()` because the
   icon swap reads better as instantaneous. */
.qa-scan-name-item,
.qa-scan-desc-item {
  height: 1.4em;
  line-height: 1.4em;
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.qa-scan-name-item {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.qa-scan-desc-item {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: -0.003em;
}
@keyframes qa-scan-text-roll {
  /* 14 items × ~7.14% per slot. Each slot holds for 5% then transitions
     over 2.14% to the next. Result: text feels like it slides smoothly
     while the icon (on steps()) snaps in sync. */
  0%    { transform: translateY(0); }
  5%    { transform: translateY(0); }
  7.14% { transform: translateY(-1.4em); }
  12.14%{ transform: translateY(-1.4em); }
  14.28%{ transform: translateY(-2.8em); }
  19.28%{ transform: translateY(-2.8em); }
  21.42%{ transform: translateY(-4.2em); }
  26.42%{ transform: translateY(-4.2em); }
  28.56%{ transform: translateY(-5.6em); }
  33.56%{ transform: translateY(-5.6em); }
  35.70%{ transform: translateY(-7.0em); }
  40.70%{ transform: translateY(-7.0em); }
  42.84%{ transform: translateY(-8.4em); }
  47.84%{ transform: translateY(-8.4em); }
  49.98%{ transform: translateY(-9.8em); }
  54.98%{ transform: translateY(-9.8em); }
  57.12%{ transform: translateY(-11.2em); }
  62.12%{ transform: translateY(-11.2em); }
  64.26%{ transform: translateY(-12.6em); }
  69.26%{ transform: translateY(-12.6em); }
  71.40%{ transform: translateY(-14.0em); }
  76.40%{ transform: translateY(-14.0em); }
  78.54%{ transform: translateY(-15.4em); }
  83.54%{ transform: translateY(-15.4em); }
  85.68%{ transform: translateY(-16.8em); }
  90.68%{ transform: translateY(-16.8em); }
  92.82%{ transform: translateY(-18.2em); }
  97.82%{ transform: translateY(-18.2em); }
  100%  { transform: translateY(-19.6em); }
}

/* Counter chip — small text version of "N checks" */
.qa-scan-counter {
  display: inline-block;
}

/* Mobile (≤ 480px): tighten the card and shrink the icon */
@media (max-width: 480px) {
  .qa-prog-scanner { padding: 12px 14px; }
  .qa-scan-icon-wrap { width: 42px; height: 42px; }
  .qa-scan-icon-item {
    width: 42px;
    height: 42px;
    font-size: 1.3rem;
  }
  @keyframes qa-scan-icon-roll {
    from { transform: translateY(0); }
    to   { transform: translateY(calc(-42px * var(--qa-scan-n))); }
  }
  .qa-scan-name-item { font-size: 0.92rem; }
  .qa-scan-desc-item { font-size: 0.74rem; }
}

.qa-prog-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.qa-prog-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  background: white;
  border: 1px solid var(--border-soft);
  border-radius: 100px;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--text);
  transition: transform 180ms ease;
}
.qa-prog-chip.empty {
  opacity: 0.4;
}
.qa-prog-chip-dot {
  width: 7px;
  height: 7px;
  border-radius: 100px;
}
.qa-prog-chip-label {
  color: var(--text-muted);
  font-weight: 500;
}
.qa-prog-chip-val {
  font-weight: 800;
  font-feature-settings: "tnum" 1, "lnum" 1;
  color: var(--text);
}

/* ──────────────────────────────────────────────
   Summary cards row (results header KPIs)
   ────────────────────────────────────────────── */
.qa-summary-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin: 0.4rem 0 1.2rem 0;
}
@media (max-width: 1100px) {
  .qa-summary-row { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 720px) {
  .qa-summary-row { grid-template-columns: repeat(2, 1fr); }
}

.qa-summary-card {
  background: var(--surface-2);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  transition: transform 180ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 180ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.qa-summary-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(61,13,26,0.06);
}
.qa-summary-card-label {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 10px;
}
.qa-summary-card-dot {
  width: 9px;
  height: 9px;
  border-radius: 100px;
  display: inline-block;
  background: rgba(61,13,26,0.2);
}
.qa-summary-card-value {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1;
  font-feature-settings: "tnum" 1, "lnum" 1;
  color: var(--text);
}
.qa-summary-card-sub {
  margin-top: 7px;
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.35;
}

/* Severity-tinted variants (only when count > 0) */
.qa-summary-card.sev-critical {
  background: linear-gradient(178deg, #fef0f0 0%, #faf6f1 95%);
  border-color: rgba(185,28,28,0.22);
}
.qa-summary-card.sev-critical .qa-summary-card-dot { background: #b91c1c; box-shadow: 0 0 0 3px rgba(185,28,28,0.10); }
.qa-summary-card.sev-critical .qa-summary-card-value { color: #7f1414; }

.qa-summary-card.sev-warning {
  background: linear-gradient(178deg, #fef6e3 0%, #faf6f1 95%);
  border-color: rgba(180,83,9,0.22);
}
.qa-summary-card.sev-warning .qa-summary-card-dot { background: #b45309; box-shadow: 0 0 0 3px rgba(180,83,9,0.10); }
.qa-summary-card.sev-warning .qa-summary-card-value { color: #7a3805; }

.qa-summary-card.sev-nit {
  background: linear-gradient(178deg, #eef6fc 0%, #faf6f1 95%);
  border-color: rgba(7,89,133,0.20);
}
.qa-summary-card.sev-nit .qa-summary-card-dot { background: #075985; box-shadow: 0 0 0 3px rgba(7,89,133,0.10); }
.qa-summary-card.sev-nit .qa-summary-card-value { color: #044067; }

.qa-summary-card.sev-ok {
  background: linear-gradient(178deg, #ecfdf4 0%, #faf6f1 95%);
  border-color: rgba(4,120,87,0.20);
}
.qa-summary-card.sev-ok .qa-summary-card-dot { background: #047857; box-shadow: 0 0 0 3px rgba(4,120,87,0.10); }
.qa-summary-card.sev-ok .qa-summary-card-value { color: #035d44; }

/* Empty state (count = 0) — neutral, no tint */
.qa-summary-card.empty {
  background: var(--surface-2);
  border-color: var(--border-soft);
}
.qa-summary-card.empty .qa-summary-card-value {
  color: rgba(61,13,26,0.30);
}
.qa-summary-card.empty .qa-summary-card-dot {
  background: rgba(61,13,26,0.20);
  box-shadow: none;
}

/* Score card — most prominent (burgundy + glow) */
.qa-summary-card.score {
  background: linear-gradient(150deg, #3d0d1a 0%, #5c1428 65%, #3d0d1a 100%);
  border-color: rgba(61,13,26,0.30);
  color: white;
}
.qa-summary-card.score::before {
  content: "";
  position: absolute;
  top: -30px; right: -20px; width: 160px; height: 160px;
  background: radial-gradient(circle, rgba(233,78,119,0.32) 0%, transparent 65%);
  pointer-events: none;
}
.qa-summary-card.score .qa-summary-card-label { color: rgba(255,255,255,0.70); }
.qa-summary-card.score .qa-summary-card-value { color: white; position: relative; z-index: 1; }
.qa-summary-card.score .qa-summary-card-value .qa-summary-card-denom {
  font-size: 1.1rem;
  font-weight: 600;
  opacity: 0.55;
  margin-left: 2px;
}
.qa-summary-card.score .qa-summary-card-sub { color: rgba(255,255,255,0.70); }
.qa-summary-card.score .qa-summary-card-dot {
  background: var(--accent);
  box-shadow: 0 0 12px rgba(233,78,119,0.5);
}

/* Cost card — subtle warm tint */
.qa-summary-card.cost {
  background: linear-gradient(178deg, var(--surface-2) 0%, #f4ece4 100%);
}

/* ──────────────────────────────────────────────
   Slide navigator — horizontal timeline track
   Dark panel with one colored brick per slide. Section names labeled below.
   ────────────────────────────────────────────── */
/* The navigator uses position: fixed. Visibility is toggled via a body
   class (`qa-nav-visible`) set/cleared by an IntersectionObserver that
   watches a sentinel (#qa-nav-trigger) placed right after the overview
   panel. The nav appears when the user scrolls past the sentinel and
   disappears when the user scrolls back up to it. */
.qa-nav {
  position: fixed;
  top: 3.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: min(calc(100vw - 3rem), 1200px);
  z-index: 200;
  background: linear-gradient(180deg, #14040a 0%, #1f0612 100%);
  border-radius: var(--radius);
  padding: 12px 16px 10px;
  box-shadow: 0 10px 28px rgba(20, 4, 10, 0.32);
  border: 1px solid rgba(255,255,255,0.05);
  opacity: 0;
  pointer-events: none;
  transform: translate(-50%, -10px);
  transition: opacity 220ms ease, transform 260ms ease;
}
body.qa-nav-visible .qa-nav {
  opacity: 1;
  pointer-events: auto;
  transform: translate(-50%, 0);
}

.qa-nav-spacer { display: none; }
.qa-nav-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}
.qa-nav-title {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-weight: 700;
  color: rgba(255,255,255,0.55);
}
.qa-nav-legend {
  display: inline-flex;
  gap: 10px;
  font-size: 0.65rem;
  color: rgba(255,255,255,0.55);
}
.qa-nav-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.qa-nav-legend-swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.qa-nav-track {
  display: flex;
  align-items: stretch;
  gap: 0;
  width: 100%;
  overflow: visible;
}

.qa-nav-section-group {
  display: flex;
  align-items: stretch;
  gap: 2px;
  /* Proportional to slide count → sections with more slides take more width.
     Inner blocks distribute equally inside their group. */
  flex: var(--qa-block-count, 1) 1 0;
  min-width: 0;
}
/* Section separator — thin vertical gap between groups */
.qa-nav-sep {
  flex: 0 0 10px;
  align-self: stretch;
  background: transparent;
  position: relative;
}
.qa-nav-sep::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 4px;
  bottom: 4px;
  width: 1px;
  background: rgba(255,255,255,0.18);
}

.qa-nav-block {
  /* Auto-fit: every block shares the row equally — all slides always on screen,
     never horizontal scroll. Min-width keeps thumbs vaguely visible at 80+ slides. */
  flex: 1 1 0;
  min-width: 6px;
  height: 52px;
  display: block;
  position: relative;
  overflow: hidden;
  border: 2px solid;
  border-radius: 4px;
  background: rgba(255,255,255,0.04);
  cursor: pointer;
  text-decoration: none !important;
  transition: flex-grow 220ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              min-width 220ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              height 220ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 180ms ease, filter 100ms ease;
  user-select: none;
}
/* Slide dimmed because current filter would hide its card */
.qa-nav-block.filtered-out {
  opacity: 0.32;
}
.qa-nav-block.filtered-out:hover {
  opacity: 1;
}

/* ───── Dock magnification ─────
   The hovered block grows to 130px min; ±1 to 70px; ±2 to 36px. Implemented
   with sibling combinators + :has() so layout reflows smoothly. Other blocks
   keep flex:1 and shrink proportionally to make room. */

/* Hovered */
.qa-nav-block:hover {
  flex-grow: 14;
  min-width: 130px;
  height: 84px;
  z-index: 6;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.6);
}

/* ±1 siblings */
.qa-nav-block:has(+ .qa-nav-block:hover),
.qa-nav-block:hover + .qa-nav-block {
  flex-grow: 6;
  min-width: 70px;
  height: 68px;
  z-index: 5;
}

/* ±2 siblings */
.qa-nav-block:has(+ .qa-nav-block + .qa-nav-block:hover),
.qa-nav-block:hover + .qa-nav-block + .qa-nav-block {
  flex-grow: 3;
  min-width: 36px;
  height: 58px;
  z-index: 4;
}
.qa-nav-block img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.qa-nav-block-no-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 0.95rem;
  font-weight: 800;
  font-feature-settings: "tnum" 1, "lnum" 1;
}
.qa-nav-block-no-thumb.sev-critical { background: #e94e77; color: white; }
.qa-nav-block-no-thumb.sev-warning  { background: #f0a429; color: #2e0a16; }
.qa-nav-block-no-thumb.sev-nit      { background: #4b8ef0; color: white; }
.qa-nav-block-no-thumb.sev-ok       { background: #2dba8a; color: white; }
.qa-nav-block-no-thumb.skipped      { background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.45); }

.qa-nav-block-num {
  position: absolute;
  top: 3px;
  left: 3px;
  background: rgba(20, 4, 10, 0.88);
  color: rgba(255,255,255,0.96);
  font-size: 0.66rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 3px;
  font-feature-settings: "tnum" 1, "lnum" 1;
  letter-spacing: 0.02em;
  z-index: 2;
  pointer-events: none;
  opacity: 0;
  transition: opacity 140ms ease;
}
/* Badge appears on magnified blocks (hovered + ±1/±2 neighbors) */
.qa-nav-block:hover .qa-nav-block-num,
.qa-nav-block:has(+ .qa-nav-block:hover) .qa-nav-block-num,
.qa-nav-block:hover + .qa-nav-block .qa-nav-block-num,
.qa-nav-block:has(+ .qa-nav-block + .qa-nav-block:hover) .qa-nav-block-num,
.qa-nav-block:hover + .qa-nav-block + .qa-nav-block .qa-nav-block-num {
  opacity: 1;
}
/* Severity stripe at the bottom of the thumbnail */
.qa-nav-block-stripe {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  z-index: 2;
}

.qa-nav-block:hover {
  transform: translateY(-3px) scale(1.04);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.55);
  filter: brightness(1.08);
  z-index: 3;
}
.qa-nav-block:active { transform: translateY(0); }

.qa-nav-block.sev-critical { border-color: #e94e77; }
.qa-nav-block.sev-warning  { border-color: #f0a429; }
.qa-nav-block.sev-nit      { border-color: #4b8ef0; }
.qa-nav-block.sev-ok       { border-color: #2dba8a; }
.qa-nav-block.sev-critical .qa-nav-block-stripe { background: #e94e77; }
.qa-nav-block.sev-warning  .qa-nav-block-stripe { background: #f0a429; }
.qa-nav-block.sev-nit      .qa-nav-block-stripe { background: #4b8ef0; }
.qa-nav-block.sev-ok       .qa-nav-block-stripe { background: #2dba8a; }
.qa-nav-block.skipped {
  border-color: rgba(255,255,255,0.18);
  filter: grayscale(0.55) brightness(0.72);
}
.qa-nav-block.skipped:hover {
  filter: grayscale(0.25) brightness(0.95);
}
.qa-nav-block.skipped .qa-nav-block-stripe {
  background: rgba(255,255,255,0.20);
}

/* Section labels row — widths match the section group above (same flex weights) */
.qa-nav-labels {
  display: flex;
  align-items: flex-start;
  margin-top: 8px;
  gap: 0;
  width: 100%;
}
.qa-nav-label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
  padding: 0 4px;
  overflow: hidden;
  flex: var(--qa-block-count, 1) 1 0;
}
.qa-nav-label-sep {
  flex: 0 0 0px;
}
.qa-nav-label-name {
  font-size: 0.66rem;
  font-weight: 700;
  color: rgba(255,255,255,0.75);
  letter-spacing: 0.01em;
  text-transform: capitalize;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 100%;
  line-height: 1.2;
}
.qa-nav-label-range {
  font-size: 0.58rem;
  color: rgba(255,255,255,0.42);
  font-weight: 500;
  font-feature-settings: "tnum" 1, "lnum" 1;
  margin-top: 1px;
}
.qa-nav-label-sep {
  flex: 0 0 6px;
}

/* Section divider above slide cards */
.qa-section-divider {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 1.6rem 0 0.6rem 0;
  padding-bottom: 6px;
  border-bottom: 1px dashed rgba(61,13,26,0.16);
  scroll-margin-top: 90px;
}
.qa-section-divider-num {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-weight: 700;
  color: var(--accent);
}
.qa-section-divider-name {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text);
  flex: 1;
}
.qa-section-divider-meta {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-weight: 500;
}

/* Anchor offset on slide cards so the sticky thumbnail navigator doesn't cover
   them on jump. Navigator is ~130px tall when sticky; Streamlit header adds
   ~56px; total ~200px clearance keeps the slide title visible under the nav. */
.qa-slide-card,
.qa-section-divider { scroll-margin-top: 200px; }

/* ──────────────────────────────────────────────
   Buenas prácticas tab — refined, Kowalski-flavoured
   White cards · large numerals · hairline dividers · pink used sparingly
   ────────────────────────────────────────────── */
.qa-bp-wrapper {
  max-width: 880px;
  margin: 0 auto;
  padding: 1rem 0 3rem 0;
}

/* ----- Header ----- */
.qa-bp-header {
  margin: 0 0 3rem 0;
}
.qa-bp-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.qa-bp-eyebrow::before {
  content: "";
  width: 18px;
  height: 1px;
  background: var(--accent);
}
.qa-bp-title {
  font-size: 2.4rem !important;
  font-weight: 700 !important;
  letter-spacing: -0.034em !important;
  color: var(--text-primary) !important;
  margin: 0 0 14px 0 !important;
  line-height: 1.08 !important;
}
.qa-bp-sub {
  font-size: 1.02rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0;
  max-width: 60ch;
  font-weight: 400;
  letter-spacing: -0.005em;
}

/* ----- Section card ----- */
.qa-bp-section {
  background: white;
  border: 1px solid rgba(61,13,26,0.06);
  border-radius: 18px;
  padding: 38px 44px;
  margin: 0 0 1rem 0;
  transition: border-color 240ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 240ms ease;
  box-shadow: 0 1px 2px rgba(61,13,26,0.025);
}
.qa-bp-section:hover {
  border-color: rgba(233,78,119,0.15);
  box-shadow: 0 4px 16px rgba(61,13,26,0.05);
}

/* Section head: large numeral on the left, titles stack on the right */
.qa-bp-section-head {
  display: flex;
  align-items: baseline;
  gap: 24px;
  margin-bottom: 22px;
  padding-bottom: 22px;
  border-bottom: 1px solid rgba(61,13,26,0.05);
}
.qa-bp-section-num {
  font-size: 1.6rem;
  font-weight: 600;
  color: rgba(61,13,26,0.28);
  letter-spacing: -0.02em;
  font-feature-settings: "tnum" 1, "lnum" 1;
  min-width: 44px;
  line-height: 1;
  flex-shrink: 0;
}
.qa-bp-section-titles {
  flex: 1;
  min-width: 0;
}
.qa-bp-section-name {
  font-size: 1.32rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.022em;
  line-height: 1.2;
  margin: 0 0 6px 0;
}
.qa-bp-section-intro {
  font-size: 0.96rem;
  font-weight: 400;
  color: var(--text-muted);
  letter-spacing: -0.005em;
  line-height: 1.5;
  margin: 0;
}

/* ----- Item list — flat lines separated by hairlines ----- */
.qa-bp-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.qa-bp-item {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(61,13,26,0.04);
  transition: padding-left 240ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.qa-bp-item:last-child { border-bottom: none; padding-bottom: 0; }
.qa-bp-item:first-child { padding-top: 0; }
.qa-bp-item:hover { padding-left: 4px; }
.qa-bp-item:hover .qa-bp-marker { width: 22px; background: var(--accent); }

/* Subtle thin accent line replaces the chunky green check circle */
.qa-bp-marker {
  flex: 0 0 auto;
  width: 14px;
  height: 1.5px;
  background: rgba(61,13,26,0.18);
  margin-top: 0.7rem;
  border-radius: 1px;
  transition: width 240ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
              background 200ms ease;
}
.qa-bp-item-body { flex: 1; min-width: 0; }
.qa-bp-item-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.013em;
  line-height: 1.4;
  margin-bottom: 5px;
}
.qa-bp-item-detail {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.65;
  letter-spacing: -0.003em;
  font-weight: 400;
}

/* =================================================================
   BUENAS PRÁCTICAS V2 — Minsait framework (3 disciplinas)
   ================================================================= */

@keyframes qa-bp-fade-up {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes qa-bp-pulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.04); }
}

.qa-bp-v2 { max-width: 980px; }

/* ---------- HERO ---------- */
.qa-bp-hero { margin: 0 0 4rem 0; }
.qa-bp-hero-tiles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 28px;
}
.qa-bp-hero-tile {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 20px 22px;
  background: white;
  border: 1px solid rgba(61,13,26,0.08);
  border-radius: 14px;
  text-decoration: none !important;
  color: inherit !important;
  transition: transform 220ms cubic-bezier(0.25,0.46,0.45,0.94),
              box-shadow 220ms ease,
              border-color 220ms ease;
  cursor: pointer;
}
.qa-bp-hero-tile:hover {
  transform: translateY(-2px);
  border-color: rgba(233,78,119,0.3);
  box-shadow: 0 8px 24px rgba(233,78,119,0.12);
}
.qa-bp-hero-tile-num {
  flex: 0 0 auto;
  font-size: 1.55rem;
  font-weight: 700;
  color: rgba(233,78,119,0.85);
  letter-spacing: -0.02em;
  line-height: 1;
  margin-top: 2px;
}
.qa-bp-hero-tile-body { flex: 1; min-width: 0; }
.qa-bp-hero-tile-name {
  font-size: 1.08rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.018em;
  margin-bottom: 4px;
}
.qa-bp-hero-tile-method {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.01em;
  margin-bottom: 6px;
}
.qa-bp-hero-tile-sub {
  font-size: 0.84rem;
  color: var(--text-muted);
  line-height: 1.45;
}

/* ---------- PILLAR (section wrapper) ---------- */
.qa-bp-pillar {
  background: white;
  border: 1px solid rgba(61,13,26,0.06);
  border-radius: 22px;
  padding: 44px 48px;
  margin: 0 0 28px 0;
  scroll-margin-top: 80px;
  animation: qa-bp-fade-up 600ms cubic-bezier(0.25,0.46,0.45,0.94) both;
}
.qa-bp-pillar-head {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 32px;
  padding-bottom: 28px;
  border-bottom: 1px solid rgba(61,13,26,0.06);
}
.qa-bp-pillar-num {
  flex: 0 0 auto;
  font-size: 3rem;
  font-weight: 700;
  color: rgba(233,78,119,0.18);
  letter-spacing: -0.04em;
  line-height: 0.9;
  font-feature-settings: "tnum" 1, "lnum" 1;
}
.qa-bp-pillar-titles { flex: 1; min-width: 0; }
.qa-bp-pillar-overline {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 6px;
}
.qa-bp-pillar-name {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.028em;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.1;
}
.qa-bp-pillar-tagline {
  font-size: 1rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

/* ---------- Section divider inside a pillar ---------- */
.qa-bp-section-divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 32px 0 22px 0;
}
.qa-bp-section-divider::before,
.qa-bp-section-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: rgba(61,13,26,0.08);
}
.qa-bp-section-divider span {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--text-muted);
}
.qa-bp-section-sub {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
  margin-bottom: 18px;
}

/* ---------- PILLAR 1 · Pyramid block ---------- */
.qa-bp-pyramid-block {
  display: grid;
  grid-template-columns: 1.05fr 1.3fr;
  gap: 32px;
  align-items: center;
  background: linear-gradient(135deg, rgba(244,241,236,0.5) 0%, white 100%);
  border-radius: 14px;
  padding: 28px;
}
.qa-bp-pyramid-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}
.qa-bp-pyramid-svg {
  width: 100%;
  max-width: 320px;
  height: auto;
}
.qa-bp-pyr-layer {
  transition: transform 280ms cubic-bezier(0.34,1.56,0.64,1), filter 200ms ease;
  transform-origin: center;
  cursor: default;
}
.qa-bp-pyramid-svg:hover .qa-bp-pyr-layer { filter: saturate(0.6) opacity(0.6); }
.qa-bp-pyramid-svg .qa-bp-pyr-layer:hover {
  filter: saturate(1.2) opacity(1) drop-shadow(0 4px 10px rgba(233,78,119,0.35));
  transform: scale(1.04);
}
.qa-bp-pyramid-caption {
  font-size: 0.78rem;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.5;
  max-width: 280px;
}
.qa-bp-pyr-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.qa-bp-pyr-card {
  background: white;
  border: 1px solid rgba(61,13,26,0.08);
  border-left: 3px solid var(--accent);
  border-radius: 10px;
  padding: 14px 18px;
  transition: border-left-width 200ms ease, transform 200ms ease;
}
.qa-bp-pyr-card:hover {
  border-left-width: 6px;
  transform: translateX(2px);
}
.qa-bp-pyr-card-name {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.015em;
}
.qa-bp-pyr-card-tag {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}
.qa-bp-pyr-card-desc {
  font-size: 0.86rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* ---------- PILLAR 1 · Principles cards ---------- */
.qa-bp-principles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.qa-bp-principle {
  background: white;
  border: 1px solid rgba(61,13,26,0.08);
  border-radius: 14px;
  padding: 22px;
  transition: transform 220ms ease, box-shadow 220ms ease;
  display: flex;
  flex-direction: column;
}
.qa-bp-principle:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(61,13,26,0.06);
}
.qa-bp-principle-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}
.qa-bp-principle-num {
  font-size: 0.78rem;
  font-weight: 700;
  color: rgba(233,78,119,0.55);
  letter-spacing: 0.05em;
}
.qa-bp-principle-title { display: flex; align-items: baseline; gap: 8px; }
.qa-bp-principle-name {
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
.qa-bp-principle-tag {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-muted);
  font-style: italic;
}
.qa-bp-principle-desc {
  font-size: 0.86rem;
  color: var(--text-muted);
  line-height: 1.55;
  margin: 0 0 14px 0;
}
.qa-bp-principle-examples {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.qa-bp-ex {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 0.8rem;
  line-height: 1.45;
}
.qa-bp-ex-bad { background: rgba(204,80,80,0.06); border-left: 2px solid rgba(204,80,80,0.45); }
.qa-bp-ex-good { background: rgba(4,120,87,0.06); border-left: 2px solid rgba(4,120,87,0.45); }
.qa-bp-ex-tag {
  font-weight: 700;
  flex-shrink: 0;
  font-size: 0.78rem;
}
.qa-bp-ex-bad .qa-bp-ex-tag { color: rgba(180,40,40,0.85); }
.qa-bp-ex-good .qa-bp-ex-tag { color: rgba(4,120,87,0.85); }
.qa-bp-ex-txt {
  color: var(--text);
  font-style: italic;
}

/* ---------- PILLAR 1 · Build-path tabs ---------- */
.qa-bp-tabs { margin-top: 8px; }
.qa-bp-tab-input { position: absolute; opacity: 0; pointer-events: none; }
.qa-bp-tab-labels {
  display: inline-flex;
  background: rgba(61,13,26,0.05);
  padding: 4px;
  border-radius: 100px;
  gap: 4px;
  margin-bottom: 18px;
}
.qa-bp-tab-label {
  padding: 9px 22px;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 100px;
  transition: background 220ms ease, color 220ms ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.qa-bp-tab-label:hover { color: var(--text-primary); }
.qa-bp-tab-arrow {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
}
.qa-bp-tabs-build .qa-bp-tab-panel { display: none; animation: qa-bp-fade-up 400ms ease both; }
#qa-bp-buildtop:checked ~ .qa-bp-tab-labels label[for="qa-bp-buildtop"],
#qa-bp-buildbot:checked ~ .qa-bp-tab-labels label[for="qa-bp-buildbot"] {
  background: white;
  color: var(--text-primary);
  box-shadow: 0 2px 8px rgba(61,13,26,0.08);
}
#qa-bp-buildtop:checked ~ .qa-bp-tab-panels .qa-bp-build-top,
#qa-bp-buildbot:checked ~ .qa-bp-tab-panels .qa-bp-build-bot { display: block; }

.qa-bp-build-tag {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  background: rgba(233,78,119,0.08);
  padding: 5px 12px;
  border-radius: 100px;
  margin-bottom: 14px;
}
.qa-bp-steps {
  margin: 0 0 16px 0;
  padding: 0;
  list-style: none;
  counter-reset: qa-bp-step;
}
.qa-bp-steps li {
  counter-increment: qa-bp-step;
  position: relative;
  padding: 10px 0 10px 40px;
  font-size: 0.92rem;
  color: var(--text);
  border-bottom: 1px solid rgba(61,13,26,0.04);
  line-height: 1.55;
}
.qa-bp-steps li:last-child { border-bottom: none; }
.qa-bp-steps li::before {
  content: counter(qa-bp-step);
  position: absolute;
  left: 0;
  top: 10px;
  width: 26px;
  height: 26px;
  background: rgba(233,78,119,0.12);
  color: var(--accent);
  border-radius: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.78rem;
}
.qa-bp-build-when {
  background: rgba(244,241,236,0.7);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.86rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* ---------- PILLAR 2 · SCQR flow ---------- */
.qa-bp-scqr-intro,
.qa-bp-aud-intro,
.qa-bp-chart-intro,
.qa-bp-qgate-intro {
  font-size: 0.94rem;
  color: var(--text-muted);
  line-height: 1.55;
  margin-bottom: 18px;
}
.qa-bp-scqr-flow {
  display: flex;
  align-items: stretch;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.qa-bp-scqr-block {
  flex: 1 1 0;
  min-width: 180px;
  background: white;
  border: 1px solid rgba(61,13,26,0.1);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  animation: qa-bp-fade-up 500ms cubic-bezier(0.25,0.46,0.45,0.94) both;
  animation-delay: var(--qa-bp-delay, 0ms);
  transition: transform 220ms ease, border-color 220ms ease;
}
.qa-bp-scqr-block:hover {
  transform: translateY(-3px);
  border-color: rgba(233,78,119,0.3);
}
.qa-bp-scqr-optional {
  border-style: dashed;
  background: rgba(244,241,236,0.5);
}
.qa-bp-scqr-letter {
  width: 36px;
  height: 36px;
  border-radius: 100px;
  background: linear-gradient(135deg, #e94e77 0%, #d13d64 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.1rem;
  box-shadow: 0 3px 10px rgba(233,78,119,0.3);
}
.qa-bp-scqr-optional .qa-bp-scqr-letter {
  background: rgba(61,13,26,0.4);
  box-shadow: none;
}
.qa-bp-scqr-body { display: flex; flex-direction: column; gap: 4px; }
.qa-bp-scqr-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}
.qa-bp-scqr-opt-badge {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  background: rgba(61,13,26,0.06);
  padding: 2px 8px;
  border-radius: 100px;
}
.qa-bp-scqr-q {
  font-size: 0.78rem;
  color: var(--accent);
  font-weight: 600;
  letter-spacing: -0.005em;
}
.qa-bp-scqr-ex {
  font-size: 0.82rem;
  color: var(--text-muted);
  font-style: italic;
  line-height: 1.5;
  border-top: 1px solid rgba(61,13,26,0.06);
  padding-top: 8px;
  margin-top: 4px;
}
.qa-bp-scqr-arrow {
  display: flex;
  align-items: center;
  font-size: 1.4rem;
  font-weight: 600;
  color: rgba(233,78,119,0.4);
  flex-shrink: 0;
}

/* ---------- PILLAR 2 · Audience matrix ---------- */
.qa-bp-aud-matrix {
  background: white;
  border: 1px solid rgba(61,13,26,0.08);
  border-radius: 14px;
  overflow: hidden;
}
.qa-bp-aud-header-row,
.qa-bp-aud-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1.5fr;
  gap: 0;
}
.qa-bp-aud-header-row { background: rgba(244,241,236,0.6); }
.qa-bp-aud-header-cell {
  padding: 14px 18px;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  border-right: 1px solid rgba(61,13,26,0.06);
}
.qa-bp-aud-header-cell:last-child { border-right: none; }
.qa-bp-aud-row {
  border-top: 1px solid rgba(61,13,26,0.06);
}
.qa-bp-aud-row-label {
  padding: 18px;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
  background: rgba(244,241,236,0.4);
  border-right: 1px solid rgba(61,13,26,0.06);
  display: flex;
  align-items: center;
}
.qa-bp-aud-cell {
  padding: 18px;
  border-right: 1px solid rgba(61,13,26,0.06);
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: background 200ms ease;
}
.qa-bp-aud-cell:last-child { border-right: none; }
.qa-bp-aud-cell:hover { background: rgba(233,78,119,0.04); }
.qa-bp-aud-pattern {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Mono", monospace;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.02em;
}
.qa-bp-aud-meta {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}
.qa-bp-aud-desc {
  font-size: 0.84rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* ---------- PILLAR 3 · Slide anatomy ---------- */
.qa-bp-slide-anatomy {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 28px;
  align-items: center;
  background: linear-gradient(135deg, rgba(244,241,236,0.4) 0%, white 100%);
  padding: 28px;
  border-radius: 14px;
}
.qa-bp-slide-anatomy-visual {
  display: flex;
  justify-content: center;
}
.qa-bp-slide-anatomy-svg {
  width: 100%;
  max-width: 480px;
  height: auto;
  filter: drop-shadow(0 8px 24px rgba(61,13,26,0.08));
}
.qa-bp-elements-legend {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.qa-bp-elem-row {
  display: flex;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(61,13,26,0.04);
  align-items: flex-start;
}
.qa-bp-elem-row:last-child { border-bottom: none; }
.qa-bp-elem-num {
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
  border-radius: 100px;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.78rem;
  box-shadow: 0 2px 6px rgba(233,78,119,0.25);
}
.qa-bp-elem-body { flex: 1; min-width: 0; }
.qa-bp-elem-name {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.qa-bp-elem-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.45;
}

/* ---------- PILLAR 3 · Chart picker (CSS-only tabs) ---------- */
.qa-bp-chart-picker {
  background: white;
  border: 1px solid rgba(61,13,26,0.08);
  border-radius: 14px;
  padding: 6px;
}
.qa-bp-chart-input { position: absolute; opacity: 0; pointer-events: none; }
.qa-bp-chart-tabs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  background: rgba(61,13,26,0.04);
  padding: 5px;
  border-radius: 10px;
  margin-bottom: 4px;
}
.qa-bp-chart-tab {
  padding: 12px 14px;
  text-align: center;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 8px;
  transition: background 220ms ease, color 220ms ease;
}
.qa-bp-chart-tab:hover { color: var(--text-primary); }
.qa-bp-chart-panel { display: none; padding: 24px 22px 18px; animation: qa-bp-fade-up 350ms ease both; }
#qa-bp-chart-rel:checked   ~ .qa-bp-chart-tabs label[for="qa-bp-chart-rel"],
#qa-bp-chart-comp:checked  ~ .qa-bp-chart-tabs label[for="qa-bp-chart-comp"],
#qa-bp-chart-dist:checked  ~ .qa-bp-chart-tabs label[for="qa-bp-chart-dist"],
#qa-bp-chart-comp2:checked ~ .qa-bp-chart-tabs label[for="qa-bp-chart-comp2"] {
  background: white;
  color: var(--accent);
  box-shadow: 0 2px 8px rgba(61,13,26,0.06);
}
#qa-bp-chart-rel:checked   ~ .qa-bp-chart-panels .qa-bp-chart-panel-rel,
#qa-bp-chart-comp:checked  ~ .qa-bp-chart-panels .qa-bp-chart-panel-comp,
#qa-bp-chart-dist:checked  ~ .qa-bp-chart-panels .qa-bp-chart-panel-dist,
#qa-bp-chart-comp2:checked ~ .qa-bp-chart-panels .qa-bp-chart-panel-comp2 { display: block; }

.qa-bp-chart-q {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 14px;
  letter-spacing: -0.008em;
}
.qa-bp-chart-opts {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}
.qa-bp-chart-opt {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: rgba(244,241,236,0.5);
  border-radius: 8px;
  font-size: 0.88rem;
  color: var(--text);
  font-weight: 500;
  border: 1px solid transparent;
  transition: border-color 200ms ease, background 200ms ease;
}
.qa-bp-chart-opt:hover {
  background: white;
  border-color: rgba(233,78,119,0.3);
}
.qa-bp-chart-opt-dot {
  width: 8px;
  height: 8px;
  border-radius: 100px;
  background: var(--accent);
  box-shadow: 0 0 0 3px rgba(233,78,119,0.15);
  flex-shrink: 0;
}

/* ---------- PILLAR 3 · Quality gate (3 columns) ---------- */
.qa-bp-qgate {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.qa-bp-qgate-col {
  background: white;
  border: 1px solid rgba(61,13,26,0.08);
  border-top: 4px solid var(--qa-bp-qg-color, rgba(233,78,119,0.4));
  border-radius: 12px;
  padding: 22px 20px;
}
.qa-bp-qgate-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(61,13,26,0.06);
}
.qa-bp-qgate-letter {
  width: 28px;
  height: 28px;
  border-radius: 100px;
  background: var(--qa-bp-qg-color, rgba(233,78,119,0.2));
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.88rem;
}
.qa-bp-qgate-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.012em;
}
.qa-bp-qgate-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.qa-bp-qgate-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(61,13,26,0.04);
}
.qa-bp-qgate-item:last-child { border-bottom: none; }
.qa-bp-qgate-check {
  flex: 0 0 auto;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: rgba(4,120,87,0.12);
  color: rgba(4,120,87,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.7rem;
  margin-top: 2px;
}
.qa-bp-qgate-item-body { flex: 1; min-width: 0; }
.qa-bp-qgate-item-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
  line-height: 1.4;
}
.qa-bp-qgate-item-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.45;
}

/* ---------- FOOTER ---------- */
.qa-bp-footer {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-top: 32px;
  padding: 24px 28px;
  background: linear-gradient(135deg, #2d0e17 0%, #3d0d1a 100%);
  border-radius: 16px;
  color: white;
}
.qa-bp-footer-icon {
  font-size: 2.2rem;
  flex-shrink: 0;
  animation: qa-bp-pulse 2.6s ease-in-out infinite;
}
.qa-bp-footer-text { flex: 1; }
.qa-bp-footer-headline {
  font-size: 1.04rem;
  font-weight: 700;
  letter-spacing: -0.015em;
  margin-bottom: 4px;
}
.qa-bp-footer-sub {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.75);
  line-height: 1.55;
}
.qa-bp-footer-sub strong { color: var(--accent); font-weight: 700; }

/* ---------- Mobile (≤ 720px) ---------- */
@media (max-width: 720px) {
  .qa-bp-pillar { padding: 28px 22px; border-radius: 16px; }
  .qa-bp-pillar-head { gap: 14px; }
  .qa-bp-pillar-num { font-size: 2.2rem; }
  .qa-bp-pillar-name { font-size: 1.4rem; }
  .qa-bp-hero-tiles { grid-template-columns: 1fr; }
  .qa-bp-pyramid-block,
  .qa-bp-slide-anatomy { grid-template-columns: 1fr; gap: 22px; }
  .qa-bp-principles { grid-template-columns: 1fr; }
  .qa-bp-qgate { grid-template-columns: 1fr; }
  .qa-bp-chart-tabs { grid-template-columns: repeat(2, 1fr); }
  .qa-bp-scqr-flow { flex-direction: column; }
  .qa-bp-scqr-arrow { transform: rotate(90deg); margin: 0 auto; }
  .qa-bp-aud-header-row,
  .qa-bp-aud-row { grid-template-columns: 1fr; }
  .qa-bp-aud-row-label { border-right: none; border-bottom: 1px solid rgba(61,13,26,0.06); }
}

/* Skipped slide card — compact, no checklist, single clear banner */
.qa-slide-card.skipped-card {
  opacity: 0.86;
}
.qa-skipped-banner {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  background: rgba(61,13,26,0.04);
  border: 1px dashed rgba(61,13,26,0.18);
  border-radius: 10px;
  align-self: flex-start;
}
.qa-skipped-banner-label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-weight: 700;
  color: var(--accent);
}
.qa-skipped-banner-msg {
  font-size: 0.92rem;
  color: var(--text);
  letter-spacing: -0.005em;
  font-weight: 500;
}

/* All-green banner — shown when a slide has zero failing checks. Stays soft
   (mostly white) so a deck full of approved slides doesn't feel oppressive. */
.qa-slide-allgreen {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: linear-gradient(178deg, var(--status-ok-bg) 0%, white 100%);
  border: 1px solid rgba(4,120,87,0.18);
  border-radius: 10px;
}
.qa-slide-allgreen-icon {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--status-ok);
  color: white;
  border-radius: 100px;
  font-size: 1.05rem;
  font-weight: 800;
  box-shadow: 0 2px 8px rgba(4,120,87,0.25);
}
.qa-slide-allgreen-body { flex: 1; min-width: 0; }
.qa-slide-allgreen-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--status-ok);
  letter-spacing: -0.012em;
}
.qa-slide-allgreen-sub {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin-top: 2px;
  line-height: 1.45;
}

/* ──────────────────────────────────────────────
   Deck overview panel — promoted from expander
   ────────────────────────────────────────────── */
.qa-overview {
  background: var(--surface-2);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 22px 24px;
  margin: 0.4rem 0 1.6rem 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px 28px;
}
@media (max-width: 900px) {
  .qa-overview { grid-template-columns: 1fr; }
}
.qa-overview-header {
  grid-column: 1 / -1;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-soft);
  padding-bottom: 12px;
  margin-bottom: 4px;
}
.qa-overview-title {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text);
}
.qa-overview-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.qa-overview-label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-weight: 700;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}
.qa-overview-value {
  font-size: 0.92rem;
  color: var(--text);
  line-height: 1.5;
}
.qa-overview-value strong { font-weight: 700; }
.qa-overview-issues {
  list-style: none;
  padding: 0;
  margin: 4px 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.qa-overview-issue {
  font-size: 0.82rem;
  color: var(--text);
  background: rgba(255,255,255,0.5);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 7px 10px;
  line-height: 1.4;
}
.qa-overview-issue-slides {
  font-weight: 700;
  color: var(--accent);
  margin-right: 6px;
}

/* ──────────────────────────────────────────────
   Section picker (pre-run) — section toggle cards
   ────────────────────────────────────────────── */
.qa-section-picker-hint {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin: 0 0 0.6rem 0;
  line-height: 1.5;
}

/* ──────────────────────────────────────────────
   Filter pills — restyle native st.checkbox as pill toggles
   Applied globally; both filter rows use checkboxes.
   ────────────────────────────────────────────── */
[data-testid="stCheckbox"] > label {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 7px 14px !important;
  border-radius: 100px !important;
  background: var(--surface-2) !important;
  border: 1px solid var(--border-soft) !important;
  cursor: pointer !important;
  transition: background 160ms ease, border-color 160ms ease, transform 100ms ease !important;
}
[data-testid="stCheckbox"] > label:hover {
  background: var(--surface-3) !important;
  border-color: rgba(61,13,26,0.12) !important;
}
[data-testid="stCheckbox"] > label:active {
  transform: scale(0.98);
}
/* Hide the native checkbox marker — pill IS the affordance */
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child,
[data-testid="stCheckbox"] [role="checkbox"] {
  display: none !important;
}
[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  margin: 0 !important;
  color: var(--text) !important;
}
/* Checked state — accent fill */
[data-testid="stCheckbox"]:has(input:checked) > label {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}
[data-testid="stCheckbox"]:has(input:checked) > label p {
  color: white !important;
}

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

/* ──────────────────────────────────────────────
   Hero — atmospheric dark gradient with dot pattern
   Inspired by AI/data-flow visuals.
   ────────────────────────────────────────────── */
.qa-hero {
  position: relative;
  border-radius: 24px;
  padding: 64px 56px 68px 56px;
  margin: 0 0 22px 0;
  /* Hero takes most of the initial viewport — first impression should be a
     full, atmospheric statement. Clamped so it never gets absurd on
     ultrawide screens but always feels generous. */
  min-height: clamp(360px, 62vh, 560px);
  background:
    /* warm pink glow top-right */
    radial-gradient(ellipse 60% 70% at 78% 22%, rgba(233,78,119,0.55) 0%, transparent 55%),
    /* purple wash bottom-left */
    radial-gradient(ellipse 50% 60% at 22% 78%, rgba(108,55,168,0.42) 0%, transparent 55%),
    /* blue-teal accent bottom-center */
    radial-gradient(ellipse 70% 50% at 50% 110%, rgba(20,90,150,0.38) 0%, transparent 60%),
    /* subtle amber highlight top-left */
    radial-gradient(ellipse 30% 35% at 8% 8%, rgba(255,180,90,0.18) 0%, transparent 60%),
    /* base burgundy depth */
    linear-gradient(135deg, #14040a 0%, #2e0a16 45%, #3d0d1a 100%);
  color: white;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: 0 22px 64px rgba(61,13,26,0.28), 0 4px 14px rgba(61,13,26,0.14);
}

/* Dot pattern overlay — fades in from edges via mask */
.qa-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.16) 1px, transparent 1.6px);
  background-size: 16px 16px;
  background-position: 0 0;
  mask-image: linear-gradient(110deg, transparent 0%, black 22%, black 78%, transparent 100%);
  -webkit-mask-image: linear-gradient(110deg, transparent 0%, black 22%, black 78%, transparent 100%);
  pointer-events: none;
  opacity: 0.85;
}

/* Soft blurred orbs for depth */
.qa-hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(ellipse 28% 18% at 82% 38%, rgba(255,220,140,0.22) 0%, transparent 60%),
    radial-gradient(ellipse 22% 14% at 18% 62%, rgba(140,90,220,0.25) 0%, transparent 60%),
    radial-gradient(ellipse 18% 12% at 92% 78%, rgba(255,120,170,0.20) 0%, transparent 60%);
  pointer-events: none;
  filter: blur(24px);
}

.qa-hero-content {
  position: relative;
  z-index: 2;
  max-width: 720px;
}

.qa-hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 20px;
  text-shadow: 0 0 24px rgba(233,78,119,0.65);
}
.qa-hero-eyebrow::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 100px;
  background: var(--accent);
  box-shadow: 0 0 10px rgba(233,78,119,0.9);
}

.qa-hero h1 {
  color: white !important;
  font-size: clamp(2.4rem, 5vw, 3.4rem) !important;
  font-weight: 800 !important;
  letter-spacing: -0.028em !important;
  line-height: 1.04 !important;
  margin: 0 0 20px 0 !important;
  text-shadow: 0 2px 30px rgba(0,0,0,0.4);
}

.qa-hero p {
  color: rgba(255,255,255,0.82) !important;
  font-size: 1.05rem;
  line-height: 1.55;
  margin: 0;
  max-width: 62ch;
  font-weight: 400;
}

.qa-hero code {
  background: rgba(233,78,119,0.18) !important;
  color: rgba(255,255,255,0.92) !important;
  border: 1px solid rgba(233,78,119,0.35);
  padding: 1px 7px !important;
  border-radius: 4px !important;
  font-weight: 600 !important;
}

/* Small floating chips at the bottom of the hero — show what's evaluated */
.qa-hero-chips {
  position: relative;
  z-index: 2;
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.qa-hero-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 100px;
  font-size: 0.72rem;
  color: rgba(255,255,255,0.85);
  font-weight: 500;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: var(--dur-normal) var(--ease-spring);
}
.qa-hero-chip:hover {
  background: rgba(255,255,255,0.14);
  border-color: rgba(255,255,255,0.22);
}
.qa-hero-chip-dot {
  width: 5px;
  height: 5px;
  border-radius: 100px;
  background: var(--accent);
  box-shadow: 0 0 6px rgba(233,78,119,0.8);
}

/* Responsive: shrink on narrow screens */
@media (max-width: 720px) {
  .qa-hero { padding: 40px 28px; min-height: 50vh; }
  .qa-hero h1 { font-size: 2rem !important; }
}

/* ──────────────────────────────────────────────
   Slide card + checklist (per-slide layout)
   ────────────────────────────────────────────── */
.qa-slide-card {
  background: rgba(255,255,255,0.7);
  border: 1px solid var(--border-soft);
  border-left: 4px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 14px;
  transition: var(--dur-normal) var(--ease-spring);
}
.qa-slide-card:hover {
  background: rgba(255,255,255,0.92);
  box-shadow: var(--shadow-sm);
}
.qa-slide-card.sev-critical { border-left-color: var(--status-crit); }
.qa-slide-card.sev-warning  { border-left-color: var(--status-warn); }
.qa-slide-card.sev-nit      { border-left-color: #075985; }
.qa-slide-card.sev-ok       { border-left-color: var(--status-ok); }

.qa-slide-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-soft);
  flex-wrap: wrap;
}
.qa-slide-sev { font-size: 1.15rem; line-height: 1; }
.qa-slide-num {
  font-weight: 800;
  font-size: 0.98rem;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.qa-slide-score {
  font-size: 0.74rem;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 100px;
  background: var(--surface-3);
  color: var(--text-primary);
}
.qa-slide-score.sev-critical { background: var(--status-crit-bg); color: var(--status-crit); }
.qa-slide-score.sev-warning  { background: var(--status-warn-bg); color: var(--status-warn); }
.qa-slide-score.sev-nit      { background: #eef6fc; color: #075985; }
.qa-slide-score.sev-ok       { background: var(--status-ok-bg); color: var(--status-ok); }
.qa-slide-role {
  font-size: 0.7rem;
  color: var(--text-muted);
  padding: 2px 7px;
  background: rgba(61,13,26,0.04);
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
}
.qa-slide-title {
  flex: 1;
  font-size: 0.92rem;
  color: var(--text-muted);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 120px;
}

.qa-slide-body {
  display: flex;
  gap: 18px;
  align-items: flex-start;
}
.qa-slide-thumb {
  flex-shrink: 0;
  width: 210px;
}
.qa-slide-thumb img {
  width: 100%;
  border-radius: 8px;
  border: 1px solid var(--border-soft);
  display: block;
  background: var(--bg-card);
}
.qa-slide-checks { flex: 1; min-width: 0; }

/* Checklist row */
.qa-checklist {}
.qa-checklist-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid var(--border-soft);
}
.qa-checklist-item:first-child { padding-top: 0; }
.qa-checklist-item:last-child { border-bottom: none; padding-bottom: 0; }
.qa-checklist-icon {
  font-size: 1.05rem;
  font-weight: 700;
  flex-shrink: 0;
  width: 18px;
  text-align: center;
  line-height: 1.4;
}
.qa-checklist-icon.ok   { color: var(--status-ok); }
.qa-checklist-icon.fail { color: var(--status-crit); }
.qa-checklist-icon.na   { color: var(--text-faint); }
.qa-checklist-main { flex: 1; min-width: 0; }
.qa-checklist-row1 {
  display: flex;
  gap: 10px;
  align-items: baseline;
  flex-wrap: wrap;
}
.qa-checklist-label {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.88rem;
  flex-shrink: 0;
}
.qa-checklist-status {
  color: var(--text-muted);
  font-size: 0.85rem;
  line-height: 1.45;
  flex: 1;
  min-width: 0;
}
.qa-checklist-current {
  display: inline-block;
  margin-top: 5px;
  padding: 3px 8px;
  background: var(--surface-3);
  border-left: 2px solid var(--border-strong);
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-size: 0.78rem;
  color: var(--text-primary);
  max-width: 100%;
  word-break: break-word;
}
.qa-checklist-suggestion {
  margin-top: 7px;
  padding: 8px 11px;
  background: var(--accent-soft);
  border-left: 3px solid var(--accent);
  border-radius: 4px;
  font-size: 0.83rem;
  color: var(--bg-panel);
  line-height: 1.45;
}
.qa-checklist-suggestion::before {
  content: "→ ";
  color: var(--accent);
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

/* ──────────────────────────────────────────────
   MOBILE — iPhone-class viewports (≤ 480px)
   Single comprehensive block placed at the end so it overrides anything
   above. The Streamlit app is embedded full-bleed in mobile Safari; the
   default desktop spacing + fixed widths used to push slide cards and
   tabs past the viewport edge. These rules collapse / wrap / shrink the
   biggest offenders.
   ────────────────────────────────────────────── */
@media (max-width: 480px) {
  /* Tighter outer page padding */
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
    padding-top: 0.75rem !important;
  }

  /* Tab list — allow wrap so all 3 pills fit; compact padding */
  .stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap !important;
    width: 100% !important;
    padding: 4px !important;
    gap: 2px !important;
  }
  .stTabs [data-baseweb="tab"] {
    padding: 6px 12px !important;
    flex: 1 1 auto !important;
  }
  .stTabs [data-baseweb="tab"] p {
    font-size: 0.78rem !important;
  }

  /* Hero — much tighter padding + smaller type so it doesn't dominate */
  .qa-hero {
    padding: 28px 22px 30px !important;
    min-height: auto !important;
    border-radius: 16px !important;
  }
  .qa-hero h1 {
    font-size: 2rem !important;
    margin-bottom: 12px !important;
  }
  .qa-hero p {
    font-size: 0.92rem !important;
    line-height: 1.5 !important;
  }
  .qa-hero-eyebrow {
    font-size: 0.66rem !important;
    margin-bottom: 12px !important;
  }
  .qa-hero-chips {
    margin-top: 14px !important;
    gap: 6px !important;
  }
  .qa-hero-chip {
    font-size: 0.68rem !important;
    padding: 4px 9px !important;
  }

  /* Metric cards — stack vertically on narrow screens */
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }
  [data-testid="stMetric"] {
    padding: 10px 14px 12px !important;
  }
  [data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
  }

  /* File uploader — less padding */
  [data-testid="stFileUploader"] section {
    padding: 14px 16px !important;
  }

  /* Summary cards row — collapse to single column already covered, but
     ensure no min-width forces overflow */
  .qa-summary-row {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  .qa-summary-card {
    padding: 12px 14px !important;
  }
  .qa-summary-card-value {
    font-size: 1.55rem !important;
  }

  /* Slide cards — stack thumb above checks, thumb full-width */
  .qa-slide-body {
    flex-direction: column !important;
    gap: 12px !important;
  }
  .qa-slide-thumb {
    width: 100% !important;
    max-width: 320px;
  }
  .qa-slide-thumb img {
    width: 100% !important;
    height: auto !important;
  }
  .qa-slide-header {
    flex-wrap: wrap !important;
    gap: 6px !important;
  }
  .qa-slide-title {
    flex-basis: 100% !important;
    min-width: 0 !important;
    white-space: normal !important;
    text-overflow: clip !important;
  }
  .qa-slide-card {
    padding: 14px 16px !important;
    border-radius: 12px !important;
  }

  /* Checklist items inside slide cards */
  .qa-checklist-item {
    padding: 10px 0 !important;
    gap: 10px !important;
  }
  .qa-checklist-icon {
    flex: 0 0 22px !important;
    height: 22px !important;
  }

  /* Buenas prácticas — section padding tightens, header stacks */
  .qa-bp-wrapper {
    padding: 0.6rem 0 1.6rem 0 !important;
  }
  .qa-bp-title {
    font-size: 1.7rem !important;
  }
  .qa-bp-section {
    padding: 22px 18px !important;
    border-radius: 14px !important;
  }
  .qa-bp-section-head {
    flex-wrap: wrap !important;
    gap: 8px !important;
    padding-bottom: 14px !important;
    margin-bottom: 14px !important;
  }
  .qa-bp-section-num {
    font-size: 1.2rem !important;
    min-width: auto !important;
  }
  .qa-bp-section-name {
    font-size: 1.1rem !important;
  }
  .qa-bp-item {
    padding: 12px 0 !important;
    gap: 12px !important;
  }
  .qa-bp-item-title {
    font-size: 0.94rem !important;
  }
  .qa-bp-item-detail {
    font-size: 0.85rem !important;
  }

  /* Live progress dashboard — stack the percentage and meta */
  .qa-prog {
    padding: 14px 16px !important;
  }
  .qa-prog-head {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
  }
  .qa-prog-pct {
    font-size: 2.2rem !important;
    min-width: auto !important;
  }

  /* Overview panel — single column */
  .qa-overview {
    grid-template-columns: 1fr !important;
    padding: 16px 18px !important;
  }

  /* Cost panel — tighter */
  .qa-cost-panel {
    padding: 14px 16px !important;
  }
  .qa-cost-panel-value {
    font-size: 1.4rem !important;
  }

  /* Floating thumbnail navigator — make it scroll horizontally and use less
     vertical space. The dock magnification widths are luxurious on desktop
     but break the row on mobile. */
  .qa-nav {
    width: calc(100vw - 1rem) !important;
    padding: 8px 10px !important;
  }
  .qa-nav-header {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 4px !important;
    margin-bottom: 6px !important;
  }
  .qa-nav-legend {
    font-size: 0.6rem !important;
    flex-wrap: wrap !important;
  }
  .qa-nav-track {
    overflow-x: auto !important;
  }
  .qa-nav-block:hover {
    flex-grow: 1 !important;
    min-width: 50px !important;
    height: 42px !important;
  }

  /* Skipped card banner */
  .qa-skipped-banner {
    padding: 12px 14px !important;
  }

  /* General: prevent any wide element from pushing the viewport */
  body, html {
    overflow-x: hidden !important;
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


def hero(
    eyebrow_text: str,
    title: str,
    description_html: str,
    chips: list[str] | None = None,
) -> None:
    """Atmospheric hero section. Renders a dark gradient card with the
    page title and subtitle, plus optional small chips listing capabilities.

    `description_html` is rendered as-is (allows inline <code> etc.) —
    pre-escape any user-supplied content before passing.
    """
    chips_html = ""
    if chips:
        chip_items = "".join(
            f'<span class="qa-hero-chip">'
            f'<span class="qa-hero-chip-dot"></span>{_escape_html(c)}'
            f'</span>'
            for c in chips
        )
        chips_html = f'<div class="qa-hero-chips">{chip_items}</div>'

    html = (
        '<div class="qa-hero">'
        '<div class="qa-hero-content">'
        f'<div class="qa-hero-eyebrow">{_escape_html(eyebrow_text)}</div>'
        f'<h1>{_escape_html(title)}</h1>'
        f'<p>{description_html}</p>'
        '</div>'
        f'{chips_html}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_label(text: str) -> None:
    """Section divider label — uppercase, muted."""
    st.markdown(f'<span class="qa-section-label">{text}</span>', unsafe_allow_html=True)


def _inject_html_iframe(html: str, height: int = 0) -> None:
    """Render an HTML fragment (possibly containing <script>) inside an iframe.

    Streamlit deprecated `st.components.v1.html` in favour of `st.iframe`,
    but in current versions `st.iframe` only accepts a URL via `src=` —
    not a `srcdoc=` HTML string. Until that API arrives we keep using the
    legacy `components.html` (deprecation warning is harmless log noise).
    """
    import streamlit.components.v1 as components  # noqa: PLC0415  deprecation pending
    components.html(html, height=height)


def auto_scroll_to(anchor_id: str, *, delay_ms: int = 280) -> None:
    """Inject JS (via an invisible iframe) that smoothly scrolls the parent
    document to the element with `id=anchor_id`. Use sparingly — call only
    on the rerun when the target first appears, gated by st.session_state
    so it doesn't fight the user's manual scroll on subsequent reruns.
    """
    # The script runs inside an iframe but reaches up to window.parent —
    # safe since the iframe is same-origin with the Streamlit app.
    _inject_html_iframe(
        f"""
<script>
  (function() {{
    setTimeout(function() {{
      try {{
        var doc = window.parent.document;
        var t = doc.getElementById({anchor_id!r});
        if (t) t.scrollIntoView({{behavior: 'smooth', block: 'start'}});
      }} catch (e) {{ /* cross-origin or detached — ignore */ }}
    }}, {delay_ms});
  }})();
</script>
""",
        height=0,
    )


def scroll_anchor(anchor_id: str, *, top_margin_px: int = 100) -> None:
    """Render an invisible anchor div with id=anchor_id that JS scroll
    targets can reach. Uses negative margin so it doesn't add layout space."""
    st.markdown(
        f'<div id="{anchor_id}" style="position:relative;height:0;'
        f'margin-top:-{top_margin_px}px;pointer-events:none;"></div>',
        unsafe_allow_html=True,
    )


def nav_visibility_observer(trigger_id: str) -> None:
    """Inject an IntersectionObserver that toggles `body.qa-nav-visible`
    based on whether the sentinel `#trigger_id` is above the viewport.

    Behaviour:
      - Sentinel below viewport (user above it)  → class removed, nav hidden
      - Sentinel inside viewport                  → class removed, nav hidden
      - Sentinel above viewport (scrolled past)  → class added, nav visible

    Idempotent across Streamlit reruns: any previous observer is disconnected
    before a new one is bound. Cheap to call on every render.
    """
    _inject_html_iframe(
        f"""
<script>
  (function() {{
    var doc = window.parent.document;
    var trig = doc.getElementById({trigger_id!r});
    if (!trig) {{
      doc.body.classList.remove('qa-nav-visible');
      return;
    }}
    if (window.parent.__qaNavObserver) {{
      try {{ window.parent.__qaNavObserver.disconnect(); }} catch (e) {{}}
    }}
    var obs = new IntersectionObserver(function(entries) {{
      entries.forEach(function(entry) {{
        var pastTrigger = !entry.isIntersecting
                          && entry.boundingClientRect.top < 0;
        if (pastTrigger) {{
          doc.body.classList.add('qa-nav-visible');
        }} else {{
          doc.body.classList.remove('qa-nav-visible');
        }}
      }});
    }}, {{rootMargin: '0px', threshold: 0}});
    obs.observe(trig);
    window.parent.__qaNavObserver = obs;
  }})();
</script>
""",
        height=0,
    )


def live_progress_html(
    completed: int,
    total: int,
    *,
    sev_counts: dict[str, int] | None = None,
    elapsed_s: float | None = None,
    current_label: str | None = None,
    phase: str | None = None,
    indeterminate: bool = False,
) -> str:
    """Build a rich progress dashboard: big percentage + bar + per-severity
    pills + ETA + current slide + phase pill.

    `indeterminate=True` switches the bar to a sliding marquee animation —
    use during phases where total/completed don't apply (e.g. extracting
    images, running storyline).
    """
    sev_counts = sev_counts or {}
    pct = (completed / total * 100) if total > 0 else 0
    pct_int = int(round(pct))

    # ETA based on linear extrapolation of elapsed time
    eta_html = ""
    if elapsed_s and completed > 0 and completed < total:
        per_slide = elapsed_s / completed
        remaining_s = per_slide * (total - completed)
        if remaining_s < 60:
            eta_text = f"~{int(remaining_s)}s restantes"
        else:
            eta_text = f"~{int(remaining_s // 60)}m {int(remaining_s % 60)}s restantes"
        eta_html = f'<span class="qa-prog-eta">{_escape_html(eta_text)}</span>'

    counts_html = ""
    if sev_counts:
        chips = []
        for sev, color, label in (
            ("critical", "#e94e77", "Critical"),
            ("warning",  "#f0a429", "Warning"),
            ("nit",      "#4b8ef0", "Nit"),
            ("ok",       "#2dba8a", "OK"),
        ):
            n = sev_counts.get(sev, 0)
            cls = "qa-prog-chip" + (" empty" if n == 0 else "")
            chips.append(
                f'<span class="{cls}"><span class="qa-prog-chip-dot" style="background:{color}"></span>'
                f'<span class="qa-prog-chip-label">{label}</span>'
                f'<span class="qa-prog-chip-val">{n}</span></span>'
            )
        counts_html = '<div class="qa-prog-chips">' + "".join(chips) + '</div>'

    current_html = (
        f'<div class="qa-prog-current">Slide {_escape_html(str(current_label))}</div>'
        if current_label else ""
    )

    done_status = pct >= 100 and not indeterminate
    bar_class = "qa-prog-bar-fill"
    if done_status:
        bar_class += " done"
    if indeterminate:
        bar_class += " indeterminate"

    # Indeterminate bar uses width:35% animated; otherwise width = pct
    bar_style = "" if indeterminate else f"width: {pct:.1f}%;"

    phase_html = (
        f'<div class="qa-prog-phase"><span class="qa-prog-phase-dot"></span>'
        f'{_escape_html(phase)}</div>'
        if phase else ""
    )

    pct_display = "—" if indeterminate else str(pct_int)
    pct_sym = "" if indeterminate else '<span class="qa-prog-pct-sym">%</span>'

    # "Holmes investigando" scanner card. Pure CSS — three synchronized
    # rolodexes (icon / name / description) cycle vertically in lockstep
    # so each tick reveals one rich "check" with full context. A scan-line
    # animation sweeps the card horizontally so it always looks alive.
    cycler_html = ""
    if not done_status:
        # (emoji icon, check name, short description). Order is deliberate —
        # the rolodex follows the audit order so it tells a coherent story.
        _checks = [
            ("🎯", "Action title", "Sujeto + verbo + insight cuantificado"),
            ("💡", "So-what por slide", "La implicación, no solo el dato"),
            ("🔗", "Causa → consecuencia", "Evidencia antes que conclusión"),
            ("📏", "Longitud de párrafos", "Bullets de 2-3 líneas máximo"),
            ("🔤", "Tamaño de fuente", "Mínimo 9pt en cuerpo y pie"),
            ("✒️", "Fuente brand", "ForFuture Sans en todos los textos"),
            ("Aa", "Casing del título", "Sentence case, no Title Case"),
            ("🏷️", "Pie de página", "Texto + posición canónica"),
            ("📐", "Alineación del footer", "Misma posición en todas las slides"),
            ("📊", "Densidad de texto", "Máximo ~250 palabras por slide"),
            ("🔀", "Paralelismo en bullets", "Verbos o sustantivos, no mezcla"),
            ("🌐", "Anglicismos", "Cursiva o equivalente en español"),
            ("🧩", "Rol de la slide", "Cover / divider / contenido"),
            ("📖", "Storyline cross-slide", "Horizontal logic del deck"),
        ]
        n_checks = len(_checks)
        icon_items = "".join(
            f'<span class="qa-scan-icon-item">{_escape_html(icon)}</span>'
            for icon, _, _ in _checks
        )
        name_items = "".join(
            f'<span class="qa-scan-name-item">{_escape_html(name)}</span>'
            for _, name, _ in _checks
        )
        desc_items = "".join(
            f'<span class="qa-scan-desc-item">{_escape_html(desc)}</span>'
            for _, _, desc in _checks
        )
        # Each rolodex needs total height = n × line-height. We use CSS vars
        # so we don't hard-code values that drift if the list changes length.
        cycler_html = (
            f'<div class="qa-prog-scanner" style="--qa-scan-n: {n_checks}">'
            '<div class="qa-prog-scanner-sweep" aria-hidden="true"></div>'
            '<div class="qa-prog-scanner-header">'
            '<span class="qa-prog-scanner-eyebrow">🔎 Holmes investigando</span>'
            '<span class="qa-prog-scanner-status">'
            '<span class="qa-scan-radar"></span>'
            f'<span class="qa-scan-counter">{n_checks} checks</span>'
            '</span>'
            '</div>'
            '<div class="qa-prog-scanner-body">'
            '<div class="qa-scan-icon-wrap" aria-hidden="true">'
            f'<div class="qa-scan-icon-roll">{icon_items}</div>'
            '</div>'
            '<div class="qa-scan-text">'
            f'<div class="qa-scan-name-wrap"><div class="qa-scan-name-roll">{name_items}</div></div>'
            f'<div class="qa-scan-desc-wrap"><div class="qa-scan-desc-roll">{desc_items}</div></div>'
            '</div>'
            '</div>'
            '</div>'
        )

    return (
        '<div class="qa-prog">'
        '<div class="qa-prog-head">'
        f'<div class="qa-prog-pct">{pct_display}{pct_sym}</div>'
        '<div class="qa-prog-meta">'
        f'<div class="qa-prog-fraction"><strong>{completed}</strong> / {total} slides analizados</div>'
        f'{eta_html}'
        f'{current_html}'
        '</div>'
        '</div>'
        '<div class="qa-prog-bar-track">'
        f'<div class="{bar_class}" style="{bar_style}"></div>'
        '</div>'
        f'{cycler_html}'
        f'{counts_html}'
        f'{phase_html}'
        '</div>'
    )


def best_practices_html() -> str:
    """Render the dynamic "Buenas prácticas" panel built around the Minsait
    "Presentaciones estructuradas" framework.

    Structure (3 disciplinas):
      1. Estructurar ideas — Pyramid + 3 principios (Sintetizar / Agrupar / Ordenar)
      2. Storytelling      — S-C-(Q)-R + adaptación por audiencia
      3. Plasmar en papel  — 8 elementos + chart picker + quality gate

    All interactivity is pure CSS (input[type=radio]:checked selector hack)
    so the panel renders inside st.markdown without needing components.html.
    """

    # ------------------------------------------------------------------
    # PILLAR 1 — Estructurar ideas (Pyramid + 3 principles)
    # ------------------------------------------------------------------
    pyramid_svg = '''
<svg class="qa-bp-pyramid-svg" viewBox="0 0 360 260" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="qaPyrTop" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#e94e77"/>
      <stop offset="100%" stop-color="#d13d64"/>
    </linearGradient>
    <linearGradient id="qaPyrMid" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#f18ba6"/>
      <stop offset="100%" stop-color="#e94e77"/>
    </linearGradient>
    <linearGradient id="qaPyrBot" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fbd5de"/>
      <stop offset="100%" stop-color="#f18ba6"/>
    </linearGradient>
  </defs>
  <g class="qa-bp-pyr-layer qa-bp-pyr-top">
    <polygon points="180,20 220,80 140,80" fill="url(#qaPyrTop)"/>
    <text x="180" y="58" text-anchor="middle" fill="white" font-weight="700" font-size="11">Gov. thought</text>
  </g>
  <g class="qa-bp-pyr-layer qa-bp-pyr-mid">
    <polygon points="140,85 220,85 260,150 100,150" fill="url(#qaPyrMid)"/>
    <text x="180" y="124" text-anchor="middle" fill="white" font-weight="700" font-size="11">Líneas clave</text>
  </g>
  <g class="qa-bp-pyr-layer qa-bp-pyr-bot">
    <polygon points="100,155 260,155 310,235 50,235" fill="url(#qaPyrBot)"/>
    <text x="180" y="200" text-anchor="middle" fill="#2d0e17" font-weight="700" font-size="11">Soporte (datos · facts)</text>
  </g>
</svg>'''

    pyramid_layers = [
        ("Governing thought", "Síntesis principal", "Responde la pregunta central del lector. Una afirmación convincente, breve y clara — no un resumen."),
        ("Líneas clave", "Cómo & por qué", "Acciones y razones que sostienen el governing thought. MECE entre sí. Mismo nivel de abstracción."),
        ("Soporte", "Hechos & datos", "Pertinente, suficiente y basado en hechos. Cada línea clave tiene su propio bloque de soporte."),
    ]
    pyramid_layers_html = "".join(
        f'<div class="qa-bp-pyr-card">'
        f'<div class="qa-bp-pyr-card-name">{_escape_html(name)}</div>'
        f'<div class="qa-bp-pyr-card-tag">{_escape_html(tag)}</div>'
        f'<div class="qa-bp-pyr-card-desc">{_escape_html(desc)}</div>'
        f'</div>'
        for name, tag, desc in pyramid_layers
    )

    principles = [
        ("01", "Sintetizar", "no resumir",
         "El nivel superior sintetiza al inferior — no parafrasea. Si parafraseas, no aportas 'so-what'.",
         "❌ Resumen", "Mis clientes hacen más reclamaciones por Contact Center.",
         "✅ Síntesis", "¡Necesito un plan de choque para implementar un Contact Center avanzado!"),
        ("02", "Agrupar", "MECE",
         "Mutually Exclusive, Collectively Exhaustive. Las ideas del mismo nivel pertenecen al mismo tipo: razones, causas, pasos, partes.",
         "❌ Mezclado", "Costos, equipo, junio 2026, ROI.",
         "✅ MECE", "Costos / Ingresos / Margen (todos componentes financieros)."),
        ("03", "Ordenar", "lógicamente",
         "3 órdenes válidos: cronológico (etapas), de grado (más → menos importante), estructural (descomposición MECE).",
         "❌ Random", "Renegociar contrato, redefinir proceso, reducir costes.",
         "✅ De grado", "Reducir costes (8%), redefinir proceso (5%), renegociar (3%)."),
    ]
    principles_html = "".join(
        f'<article class="qa-bp-principle">'
        f'<div class="qa-bp-principle-head">'
        f'<span class="qa-bp-principle-num">{_escape_html(num)}</span>'
        f'<div class="qa-bp-principle-title">'
        f'<span class="qa-bp-principle-name">{_escape_html(name)}</span>'
        f'<span class="qa-bp-principle-tag">{_escape_html(tag)}</span>'
        f'</div></div>'
        f'<p class="qa-bp-principle-desc">{_escape_html(desc)}</p>'
        f'<div class="qa-bp-principle-examples">'
        f'<div class="qa-bp-ex qa-bp-ex-bad"><span class="qa-bp-ex-tag">{_escape_html(bad_tag)}</span><span class="qa-bp-ex-txt">{_escape_html(bad_txt)}</span></div>'
        f'<div class="qa-bp-ex qa-bp-ex-good"><span class="qa-bp-ex-tag">{_escape_html(good_tag)}</span><span class="qa-bp-ex-txt">{_escape_html(good_txt)}</span></div>'
        f'</div></article>'
        for num, name, tag, desc, bad_tag, bad_txt, good_tag, good_txt in principles
    )

    # Bottom-up vs Top-down toggle (CSS-only tabs)
    buildpath_html = '''
<div class="qa-bp-tabs qa-bp-tabs-build">
  <input type="radio" id="qa-bp-buildtop" name="qa-bp-build" class="qa-bp-tab-input" checked>
  <input type="radio" id="qa-bp-buildbot" name="qa-bp-build" class="qa-bp-tab-input">
  <div class="qa-bp-tab-labels">
    <label for="qa-bp-buildtop" class="qa-bp-tab-label"><span class="qa-bp-tab-arrow">↓</span> Top-down</label>
    <label for="qa-bp-buildbot" class="qa-bp-tab-label"><span class="qa-bp-tab-arrow">↑</span> Bottom-up</label>
  </div>
  <div class="qa-bp-tab-panels">
    <div class="qa-bp-tab-panel qa-bp-build-top">
      <div class="qa-bp-build-tag">Desde el mensaje general</div>
      <ol class="qa-bp-steps">
        <li>Plantear la pregunta del lector.</li>
        <li>Dar la respuesta (governing thought).</li>
        <li>Desarrollar la línea clave que explica esa respuesta.</li>
        <li>Estructurar los puntos de apoyo (¿cómo? ¿por qué?).</li>
      </ol>
      <div class="qa-bp-build-when">Mejor para: <strong>alta dirección</strong> — van al grano, ya conocen el contexto.</div>
    </div>
    <div class="qa-bp-tab-panel qa-bp-build-bot">
      <div class="qa-bp-build-tag">Desde los hechos</div>
      <ol class="qa-bp-steps">
        <li>Listar conclusiones como ideas completas (con verbos).</li>
        <li>Buscar patrones para agrupar.</li>
        <li>Escribir una síntesis por grupo (síntesis A, B…).</li>
        <li>Síntesis general → governing thought del storyline.</li>
      </ol>
      <div class="qa-bp-build-when">Mejor para: <strong>directivo intermedio</strong> — necesita ver el razonamiento.</div>
    </div>
  </div>
</div>'''

    # ------------------------------------------------------------------
    # PILLAR 2 — Storytelling (S-C-Q-R + audience matrix)
    # ------------------------------------------------------------------
    scqr_blocks = [
        ("S", "Situación", "¿Dónde estamos ahora?", "Durante los últimos 10 años hemos disfrutado de un monopolio en nuestros mercados clave."),
        ("C", "Complicación", "Algo cambió", "Ahora la desregulación nos está abriendo a la competencia."),
        ("Q", "Pregunta", "¿Qué hay que resolver?", "¿Cómo vamos a responder?", "opcional"),
        ("R", "Resolución", "Lo que querés que haga la audiencia", "Lanzar una nueva campaña de marketing + programa de fidelización."),
    ]
    scqr_html = ""
    for idx, block in enumerate(scqr_blocks, start=1):
        letter, name, q, ex = block[0], block[1], block[2], block[3]
        is_optional = len(block) > 4
        opt_class = " qa-bp-scqr-optional" if is_optional else ""
        opt_badge = '<span class="qa-bp-scqr-opt-badge">opcional</span>' if is_optional else ""
        scqr_html += (
            f'<div class="qa-bp-scqr-block{opt_class}" style="--qa-bp-delay: {idx * 80}ms">'
            f'<div class="qa-bp-scqr-letter">{letter}</div>'
            f'<div class="qa-bp-scqr-body">'
            f'<div class="qa-bp-scqr-name">{_escape_html(name)}{opt_badge}</div>'
            f'<div class="qa-bp-scqr-q">{_escape_html(q)}</div>'
            f'<div class="qa-bp-scqr-ex">"{_escape_html(ex)}"</div>'
            f'</div></div>'
        )
        if idx < len(scqr_blocks):
            scqr_html += '<div class="qa-bp-scqr-arrow" aria-hidden="true">→</div>'

    # Indexed as [row][col]: row 0 = Alta dirección, row 1 = Mando medio
    #                        col 0 = Inconsciente,    col 1 = Consciente
    audience_grid = [
        [  # Alta dirección
            ("S-C-R", "Inconsciente", "Relajada, baja inercia al cambio. Necesita ver la situación y complicación antes de la resolución."),
            ("R + S-C en backup", "Consciente", "Implicada, va al grano. La respuesta primero; el contexto en backup por si pregunta."),
        ],
        [  # Mando medio
            ("S-C-Q-R", "Inconsciente", "Impaciente pero inconsciente. Necesita la pregunta explícita para enganchar."),
            ("S-C-R", "Consciente", "Sensible al problema. Sin pregunta, ya sabe qué se está discutiendo."),
        ],
    ]

    def _aud_cell(pattern: str, aware: str, desc: str) -> str:
        return (
            '<div class="qa-bp-aud-cell">'
            f'<div class="qa-bp-aud-pattern">{_escape_html(pattern)}</div>'
            f'<div class="qa-bp-aud-meta">'
            f'<span class="qa-bp-aud-aware">{_escape_html(aware)}</span>'
            f'</div>'
            f'<div class="qa-bp-aud-desc">{_escape_html(desc)}</div>'
            '</div>'
        )

    aud_row_labels = ["Alta dirección", "Mando medio"]
    aud_rows_html = ""
    for row_label, row_cells in zip(aud_row_labels, audience_grid):
        aud_rows_html += (
            '<div class="qa-bp-aud-row">'
            f'<div class="qa-bp-aud-row-label">{_escape_html(row_label)}</div>'
            + _aud_cell(*row_cells[0])
            + _aud_cell(*row_cells[1])
            + '</div>'
        )

    # ------------------------------------------------------------------
    # PILLAR 3 — Plasmar en papel (8 elements + chart picker + quality gate)
    # ------------------------------------------------------------------
    # Schematic SVG of a slide with numbered hotspots for the 8 elements.
    slide_anatomy_svg = '''
<svg class="qa-bp-slide-anatomy-svg" viewBox="0 0 480 280" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <!-- Slide canvas -->
  <rect x="10" y="10" width="460" height="260" fill="white" stroke="rgba(61,13,26,0.15)" stroke-width="1" rx="8"/>
  <!-- 6: Navigator (top-right) -->
  <rect x="380" y="22" width="80" height="14" fill="rgba(233,78,119,0.08)" rx="3"/>
  <circle cx="455" cy="29" r="9" fill="#e94e77"/>
  <text x="455" y="33" text-anchor="middle" fill="white" font-weight="700" font-size="10">6</text>
  <!-- 1: Kicker -->
  <rect x="24" y="22" width="120" height="10" fill="rgba(233,78,119,0.18)" rx="2"/>
  <circle cx="20" cy="27" r="9" fill="#e94e77"/>
  <text x="20" y="31" text-anchor="middle" fill="white" font-weight="700" font-size="10">1</text>
  <!-- 2: Title -->
  <rect x="24" y="42" width="350" height="18" fill="rgba(45,14,23,0.85)" rx="2"/>
  <circle cx="20" cy="51" r="9" fill="#e94e77"/>
  <text x="20" y="55" text-anchor="middle" fill="white" font-weight="700" font-size="10">2</text>
  <!-- 3: Tipo de slide -->
  <rect x="410" y="70" width="50" height="10" fill="rgba(108,55,168,0.18)" rx="2"/>
  <circle cx="420" cy="92" r="9" fill="#e94e77"/>
  <text x="420" y="96" text-anchor="middle" fill="white" font-weight="700" font-size="10">3</text>
  <!-- 4: Estructura del contenido (left column) -->
  <rect x="24" y="80" width="160" height="160" fill="rgba(244,241,236,0.6)" stroke="rgba(61,13,26,0.08)" rx="4"/>
  <circle cx="20" cy="85" r="9" fill="#e94e77"/>
  <text x="20" y="89" text-anchor="middle" fill="white" font-weight="700" font-size="10">4</text>
  <!-- 5: Contenido (right column with bullets) -->
  <rect x="200" y="80" width="200" height="160" fill="rgba(244,241,236,0.4)" rx="4"/>
  <line x1="210" y1="100" x2="380" y2="100" stroke="rgba(45,14,23,0.4)" stroke-width="2"/>
  <line x1="210" y1="120" x2="370" y2="120" stroke="rgba(45,14,23,0.3)" stroke-width="2"/>
  <line x1="210" y1="140" x2="375" y2="140" stroke="rgba(45,14,23,0.3)" stroke-width="2"/>
  <line x1="210" y1="160" x2="350" y2="160" stroke="rgba(45,14,23,0.3)" stroke-width="2"/>
  <circle cx="395" cy="92" r="9" fill="#e94e77"/>
  <text x="395" y="96" text-anchor="middle" fill="white" font-weight="700" font-size="10">5</text>
  <!-- 7: Footer / legend (bottom-left) -->
  <rect x="24" y="248" width="180" height="10" fill="rgba(61,13,26,0.18)" rx="2"/>
  <circle cx="20" cy="253" r="9" fill="#e94e77"/>
  <text x="20" y="257" text-anchor="middle" fill="white" font-weight="700" font-size="10">7</text>
  <!-- 8: Page number (bottom-right) -->
  <text x="450" y="260" text-anchor="middle" fill="rgba(61,13,26,0.5)" font-weight="600" font-size="11">12</text>
  <circle cx="455" cy="253" r="9" fill="#e94e77"/>
  <text x="455" y="257" text-anchor="middle" fill="white" font-weight="700" font-size="10">8</text>
</svg>'''

    slide_elements = [
        ("1", "Supertítulo (kicker)", "Eyebrow tag arriba del título. Da contexto rápido (cap. número, tema)."),
        ("2", "Título", "Action title — afirmación con insight. Lo más importante de la slide."),
        ("3", "Tipo de slide", "Preliminar · Backup · Ilustrativa · No exhaustiva · Discusión."),
        ("4", "Estructura del contenido", "Texto · Conceptos · Cifras — elegido según el mensaje."),
        ("5", "Contenido", "Sintetizado, coherente, directo, relevante. Una sola idea."),
        ("6", "Navegadores (tracker)", "Sección actual del deck. Numérico, descriptivo o visual."),
        ("7", "Leyenda / pie", "Fuente del dato, periodo, nota al pie. Exhaustivo y preciso."),
        ("8", "Composición visual", "Alineación, espaciado, jerarquía — lo que percibe el ojo."),
    ]
    elements_legend_html = "".join(
        f'<li class="qa-bp-elem-row">'
        f'<span class="qa-bp-elem-num">{num}</span>'
        f'<div class="qa-bp-elem-body">'
        f'<div class="qa-bp-elem-name">{_escape_html(name)}</div>'
        f'<div class="qa-bp-elem-desc">{_escape_html(desc)}</div>'
        f'</div></li>'
        for num, name, desc in slide_elements
    )

    # Chart picker — CSS-only with radio inputs
    chart_families = [
        ("rel", "Relación", "¿Hay correlación entre 2-3 variables?",
         ["Dispersión", "Burbujas", "Columnas ancho variable"]),
        ("comp", "Comparación", "¿Cómo se comparan magnitudes entre elementos?",
         ["Columnas", "Barras", "Líneas (datos cíclicos)"]),
        ("dist", "Distribución", "¿Cómo se distribuye una variable?",
         ["Barras", "Líneas", "Dispersión (2 vars)"]),
        ("comp2", "Composición", "¿Cómo se descompone un total?",
         ["Sectores", "Columnas apiladas 100%", "Cascada"]),
    ]
    chart_picker_html = '<div class="qa-bp-chart-picker">'
    # Radio inputs (hidden, control which panel shows)
    for i, (slug, _, _, _) in enumerate(chart_families):
        checked = " checked" if i == 0 else ""
        chart_picker_html += f'<input type="radio" id="qa-bp-chart-{slug}" name="qa-bp-chart" class="qa-bp-chart-input"{checked}>'
    # Labels (tab triggers)
    chart_picker_html += '<div class="qa-bp-chart-tabs">'
    for slug, name, _, _ in chart_families:
        chart_picker_html += f'<label for="qa-bp-chart-{slug}" class="qa-bp-chart-tab">{_escape_html(name)}</label>'
    chart_picker_html += '</div>'
    # Panels
    chart_picker_html += '<div class="qa-bp-chart-panels">'
    for slug, name, q, options in chart_families:
        opts_html = "".join(
            f'<li class="qa-bp-chart-opt"><span class="qa-bp-chart-opt-dot"></span>{_escape_html(o)}</li>'
            for o in options
        )
        chart_picker_html += (
            f'<div class="qa-bp-chart-panel qa-bp-chart-panel-{slug}">'
            f'<div class="qa-bp-chart-q">{_escape_html(q)}</div>'
            f'<ul class="qa-bp-chart-opts">{opts_html}</ul>'
            f'</div>'
        )
    chart_picker_html += '</div></div>'

    # Quality gate — 3 dimensions
    quality_gate = [
        ("A", "Formato y ortografía", "rgba(108,55,168,0.12)", [
            ("Fuente única", "Mismo formato de fuente en toda la presentación."),
            ("Sin errores", "Ortografía + gramática limpios en todos los idiomas."),
            ("Alineación H y V", "Todos los objetos y textos alineados a una grilla."),
            ("Tamaño legible", "Cuerpo ≥ 11pt; fuentes ≥ 9pt en pie y secundarios."),
            ("Espaciado equitativo", "Distribución uniforme de objetos en la slide."),
            ("Anglicismos en cursiva", "Si se usan, *italic*. Mejor reemplazar."),
        ]),
        ("B", "Consistencia del lenguaje", "rgba(233,78,119,0.12)", [
            ("Terminología coherente", "Mismas abreviaturas / acrónimos / colores en todo el deck."),
            ("Action titles", "Todos los títulos invocan o promueven acción."),
            ("Escritura paralela", "Bullets: TODOS verbos o TODOS sustantivos. No mezcla."),
            ("Verbos de acción", "Definir / implementar / evaluar — no es / son / está."),
            ("Negritas consistentes", "Énfasis siempre en el mismo tipo: cifras O conceptos."),
            ("Simplicidad", "Solo las palabras necesarias. Ni más ni menos."),
        ]),
        ("C", "Precisión y contenido", "rgba(20,90,150,0.12)", [
            ("Charts coherentes", "Pies suman 100%, mismos decimales por valor."),
            ("1 mensaje por slide", "Si necesitas 'y' o ';' para conectar, divide en dos."),
            ("Gráficos auto-explicativos", "Sin aclaraciones orales: el gráfico habla solo."),
            ("Orientación al so-what", "Conclusión clara: en el título o destacada en el cuerpo."),
            ("Framework efectivo", "La estructura encaja con las ideas que querés presentar."),
            ("Fuente del dato", "Footer del gráfico: 'Fuente: X, periodo Y'."),
        ]),
    ]
    quality_gate_html = '<div class="qa-bp-qgate">'
    for letter, name, color, items in quality_gate:
        items_html = "".join(
            f'<li class="qa-bp-qgate-item">'
            f'<span class="qa-bp-qgate-check" aria-hidden="true">✓</span>'
            f'<div class="qa-bp-qgate-item-body">'
            f'<div class="qa-bp-qgate-item-name">{_escape_html(t)}</div>'
            f'<div class="qa-bp-qgate-item-desc">{_escape_html(d)}</div>'
            f'</div></li>'
            for t, d in items
        )
        quality_gate_html += (
            f'<section class="qa-bp-qgate-col" style="--qa-bp-qg-color: {color}">'
            f'<header class="qa-bp-qgate-head">'
            f'<span class="qa-bp-qgate-letter">{letter}</span>'
            f'<span class="qa-bp-qgate-name">{_escape_html(name)}</span>'
            f'</header>'
            f'<ul class="qa-bp-qgate-list">{items_html}</ul>'
            f'</section>'
        )
    quality_gate_html += '</div>'

    # ------------------------------------------------------------------
    # Hero — 3 disciplinas tiles
    # ------------------------------------------------------------------
    hero_tiles = [
        ("01", "Estructurar", "Pirámide de Minto", "Governing thought · Líneas clave · Soporte"),
        ("02", "Storytelling", "S-C-(Q)-R", "Situación · Complicación · Pregunta · Resolución"),
        ("03", "Plasmar", "8 elementos del slide", "Action title · contenido · navegador · pie"),
    ]
    hero_tiles_html = "".join(
        f'<a href="#qa-bp-pillar-{int(num)}" class="qa-bp-hero-tile">'
        f'<span class="qa-bp-hero-tile-num">{_escape_html(num)}</span>'
        f'<div class="qa-bp-hero-tile-body">'
        f'<div class="qa-bp-hero-tile-name">{_escape_html(name)}</div>'
        f'<div class="qa-bp-hero-tile-method">{_escape_html(method)}</div>'
        f'<div class="qa-bp-hero-tile-sub">{_escape_html(sub)}</div>'
        f'</div></a>'
        for num, name, method, sub in hero_tiles
    )

    # ------------------------------------------------------------------
    # Compose the full panel
    # ------------------------------------------------------------------
    return (
        '<div class="qa-bp-wrapper qa-bp-v2">'

        # HERO
        '<div class="qa-bp-hero">'
        '<div class="qa-bp-eyebrow">📘 Minsait playbook · Presentaciones estructuradas</div>'
        '<h2 class="qa-bp-title">El estándar de presentaciones, slide por slide</h2>'
        '<p class="qa-bp-sub">Holmes audita contra <strong>tres disciplinas secuenciales</strong> que toda presentación de consultoría debe dominar. Cada pilar tiene reglas concretas — abajo está el playbook.</p>'
        f'<div class="qa-bp-hero-tiles">{hero_tiles_html}</div>'
        '</div>'

        # ============== PILLAR 1: ESTRUCTURAR ==============
        '<section class="qa-bp-pillar" id="qa-bp-pillar-1">'
        '<header class="qa-bp-pillar-head">'
        '<div class="qa-bp-pillar-num">01</div>'
        '<div class="qa-bp-pillar-titles">'
        '<div class="qa-bp-pillar-overline">Disciplina 1</div>'
        '<h3 class="qa-bp-pillar-name">Estructurar ideas</h3>'
        '<p class="qa-bp-pillar-tagline">Sin pirámide, no hay historia. Antes de redactar, sintetiza.</p>'
        '</div></header>'

        '<div class="qa-bp-pyramid-block">'
        '<div class="qa-bp-pyramid-visual">'
        f'{pyramid_svg}'
        '<div class="qa-bp-pyramid-caption">Pirámide de Minto · responde la pregunta central → desarrolla razones → soporta con datos.</div>'
        '</div>'
        f'<div class="qa-bp-pyr-cards">{pyramid_layers_html}</div>'
        '</div>'

        '<div class="qa-bp-section-divider"><span>3 principios para construirla</span></div>'
        f'<div class="qa-bp-principles">{principles_html}</div>'

        '<div class="qa-bp-section-divider"><span>Cómo construirla — dos rutas</span></div>'
        f'{buildpath_html}'
        '</section>'

        # ============== PILLAR 2: STORYTELLING ==============
        '<section class="qa-bp-pillar qa-bp-pillar-2" id="qa-bp-pillar-2">'
        '<header class="qa-bp-pillar-head">'
        '<div class="qa-bp-pillar-num">02</div>'
        '<div class="qa-bp-pillar-titles">'
        '<div class="qa-bp-pillar-overline">Disciplina 2</div>'
        '<h3 class="qa-bp-pillar-name">Storytelling</h3>'
        '<p class="qa-bp-pillar-tagline">Un conjunto de ideas en orden lógico que provoca una llamada a la acción.</p>'
        '</div></header>'

        '<div class="qa-bp-scqr-intro">Marco S-C-(Q)-R · la estructura clásica para construir cualquier historia:</div>'
        f'<div class="qa-bp-scqr-flow">{scqr_html}</div>'

        '<div class="qa-bp-section-divider"><span>Adaptación por audiencia</span></div>'
        '<div class="qa-bp-aud-intro">El mismo storyline cuenta distinto según quién escuche:</div>'
        '<div class="qa-bp-aud-matrix">'
        '<div class="qa-bp-aud-header-row">'
        '<div class="qa-bp-aud-header-cell"></div>'
        '<div class="qa-bp-aud-header-cell">Inconsciente del problema</div>'
        '<div class="qa-bp-aud-header-cell">Consciente del problema</div>'
        '</div>'
        f'{aud_rows_html}'
        '</div>'
        '</section>'

        # ============== PILLAR 3: PLASMAR EN PAPEL ==============
        '<section class="qa-bp-pillar qa-bp-pillar-3" id="qa-bp-pillar-3">'
        '<header class="qa-bp-pillar-head">'
        '<div class="qa-bp-pillar-num">03</div>'
        '<div class="qa-bp-pillar-titles">'
        '<div class="qa-bp-pillar-overline">Disciplina 3</div>'
        '<h3 class="qa-bp-pillar-name">Plasmar la historia en papel</h3>'
        '<p class="qa-bp-pillar-tagline">Una sola idea por slide. Título acción. Soporte para que llegue.</p>'
        '</div></header>'

        '<div class="qa-bp-section-sub">Los 8 elementos de una diapositiva</div>'
        '<div class="qa-bp-slide-anatomy">'
        f'<div class="qa-bp-slide-anatomy-visual">{slide_anatomy_svg}</div>'
        f'<ol class="qa-bp-elements-legend">{elements_legend_html}</ol>'
        '</div>'

        '<div class="qa-bp-section-divider"><span>Elegir el gráfico correcto</span></div>'
        '<div class="qa-bp-chart-intro">¿Qué querés mostrar? Cada familia de gráficos sirve para una pregunta distinta:</div>'
        f'{chart_picker_html}'

        '<div class="qa-bp-section-divider"><span>Quality gate · checklist final</span></div>'
        '<div class="qa-bp-qgate-intro">Las 3 dimensiones que todo deck debe cumplir antes de enviarse:</div>'
        f'{quality_gate_html}'
        '</section>'

        # FOOTER
        '<footer class="qa-bp-footer">'
        '<div class="qa-bp-footer-icon">🔍</div>'
        '<div class="qa-bp-footer-text">'
        '<div class="qa-bp-footer-headline">Holmes audita slide por slide contra este estándar</div>'
        '<div class="qa-bp-footer-sub">Más de <strong>20 checks determinísticos</strong> (action title, so-what, fuente, casing, paralelismo de bullets, verbos vinculantes, anglicismos, negritas, supertítulo, footer alineado…) + análisis semántico vía LLM cuando hay API key configurada.</div>'
        '</div></footer>'

        '</div>'
    )


def hide_nav() -> None:
    """Force-hide the navigator (and disconnect any active observer). Call on
    page renders where results aren't ready, so stale `qa-nav-visible` class
    from a previous session/file is cleared."""
    _inject_html_iframe(
        """
<script>
  (function() {
    var doc = window.parent.document;
    doc.body.classList.remove('qa-nav-visible');
    if (window.parent.__qaNavObserver) {
      try { window.parent.__qaNavObserver.disconnect(); } catch (e) {}
      window.parent.__qaNavObserver = null;
    }
  })();
</script>
""",
        height=0,
    )


def pill(text: str, variant: str = "muted") -> str:
    """Inline status pill. Variants: ok | warn | crit | info | muted."""
    return f'<span class="qa-pill {variant}">{text}</span>'


def summary_cards(cards: list[dict]) -> None:
    """Render a row of KPI cards.

    Each card dict accepts:
      - label:   uppercase label (e.g. "CRITICAL")
      - value:   big number/text (e.g. "10" or "7.7")
      - denom:   optional small denominator rendered after value (e.g. "/10")
      - sub:     optional small caption under the value (HTML allowed)
      - variant: one of: score | cost | sev-critical | sev-warning | sev-nit | sev-ok
      - empty:   bool — if True, applies neutral "empty" tint (for zero counts)
    """
    items = []
    for c in cards:
        variant = c.get("variant", "")
        if c.get("empty"):
            variant = f"{variant} empty".strip()
        denom_html = (
            f'<span class="qa-summary-card-denom">{_escape_html(c["denom"])}</span>'
            if c.get("denom") else ""
        )
        sub_html = (
            f'<div class="qa-summary-card-sub">{c["sub"]}</div>'
            if c.get("sub") else ""
        )
        items.append(
            f'<div class="qa-summary-card {variant}">'
            f'<div class="qa-summary-card-label"><span class="qa-summary-card-dot"></span>{_escape_html(c["label"])}</div>'
            f'<div class="qa-summary-card-value">{_escape_html(c["value"])}{denom_html}</div>'
            f'{sub_html}'
            '</div>'
        )
    st.markdown(
        f'<div class="qa-summary-row">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def slide_navigator(
    slides: list[dict],
    sections: list[dict] | None = None,
    thumbs: dict[int, bytes] | None = None,
    visible_slide_numbers: set[int] | None = None,
) -> None:
    """Fixed timeline navigator: one thumbnail per slide, ALL slides on screen.

    Auto-fit: blocks flex-distribute the panel width so every slide is always
    visible — no horizontal scroll. Hover triggers a macOS-dock-style local
    magnification (the hovered slide + 2 neighbors on each side grow).

    Panel is `position: fixed` so it stays visible while the user scrolls
    through the slide cards. A spacer sibling reserves its space in the flow.

    `visible_slide_numbers`, when provided, marks blocks for slides NOT in
    the set as `filtered-out` (dimmed) — so users can still see/click them
    but know the corresponding card is hidden by current filters.
    """
    import base64 as _base64

    thumbs = thumbs or {}
    visible_set = visible_slide_numbers  # None = all visible

    def _block(slide: dict) -> str:
        n = slide["slide_number"]
        sev = slide.get("severity") or "nit"
        score = slide.get("score")
        title = (slide.get("action_title") or {}).get("current_title") or ""
        if score is not None:
            tooltip = f"Slide {n} · {score}/10 · {sev.upper()}"
        else:
            tooltip = f"Slide {n} · {sev.upper()}"
        if title:
            tooltip += f" — {title[:60]}"
        classes = [f"sev-{sev}"]
        if slide.get("_skipped"):
            classes.append("skipped")
        if visible_set is not None and n not in visible_set:
            classes.append("filtered-out")
            tooltip += " · oculto por filtros"

        thumb_bytes = thumbs.get(n)
        if thumb_bytes:
            b64 = _base64.b64encode(thumb_bytes).decode("ascii")
            inner = f'<img src="data:image/png;base64,{b64}" alt="Slide {n}" />'
        else:
            no_thumb_cls = f"sev-{sev}" + (" skipped" if slide.get("_skipped") else "")
            inner = (
                f'<div class="qa-nav-block-no-thumb {no_thumb_cls}">{n}</div>'
            )

        return (
            f'<a class="qa-nav-block {" ".join(classes)}" '
            f'href="#qa-slide-{n}" title="{_escape_html(tooltip)}">'
            f'{inner}'
            f'<span class="qa-nav-block-num">{n}</span>'
            '<span class="qa-nav-block-stripe"></span>'
            '</a>'
        )

    slide_by_n = {s["slide_number"]: s for s in slides}
    total = len(slides)

    legend_html = (
        '<span class="qa-nav-legend">'
        '<span class="qa-nav-legend-item"><span class="qa-nav-legend-swatch" style="background:#e94e77"></span>Critical</span>'
        '<span class="qa-nav-legend-item"><span class="qa-nav-legend-swatch" style="background:#f0a429"></span>Warning</span>'
        '<span class="qa-nav-legend-item"><span class="qa-nav-legend-swatch" style="background:#4b8ef0"></span>Nit</span>'
        '<span class="qa-nav-legend-item"><span class="qa-nav-legend-swatch" style="background:#2dba8a"></span>OK</span>'
        '</span>'
    )
    if sections:
        title_text = f"{total} slides · {len(sections)} secciones"
    else:
        title_text = f"{total} slides"
    header_html = (
        '<div class="qa-nav-header">'
        f'<span class="qa-nav-title">{_escape_html(title_text)}</span>'
        f'{legend_html}'
        '</div>'
    )

    if sections:
        groups: list[str] = []
        labels: list[str] = []
        for i, sec in enumerate(sections):
            nums = [n for n in sec["slide_numbers"] if n in slide_by_n]
            if not nums:
                continue
            count = len(nums)
            blocks_html = "".join(_block(slide_by_n[n]) for n in nums)
            # CSS custom prop carries the block count so the section group +
            # label below can compute matching pixel widths at any zoom level.
            groups.append(
                f'<div class="qa-nav-section-group" style="--qa-block-count: {count};">'
                f'{blocks_html}'
                '</div>'
            )
            range_text = (
                f"{sec['start']}–{sec['end']}"
                if sec["start"] != sec["end"]
                else str(sec["start"])
            )
            labels.append(
                f'<div class="qa-nav-label" style="--qa-block-count: {count};">'
                f'<span class="qa-nav-label-name">{_escape_html(sec["name"])}</span>'
                f'<span class="qa-nav-label-range">{_escape_html(range_text)}</span>'
                '</div>'
            )

        sep_html = '<div class="qa-nav-sep"></div>'
        label_sep_html = '<div class="qa-nav-label-sep"></div>'
        track_html = sep_html.join(groups)
        labels_html = label_sep_html.join(labels)
        body = (
            f'<div class="qa-nav-track">{track_html}</div>'
            f'<div class="qa-nav-labels">{labels_html}</div>'
        )
    else:
        blocks_html = "".join(_block(s) for s in slides)
        body = (
            f'<div class="qa-nav-track">'
            f'<div class="qa-nav-section-group">{blocks_html}</div>'
            '</div>'
        )

    # Fixed-positioning approach: render a spacer sibling that takes the
    # navigator's vertical space in the flow so content below doesn't slide
    # under the floating panel.
    html = (
        f'<div class="qa-nav">{header_html}{body}</div>'
        '<div class="qa-nav-spacer"></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_divider(section: dict, total_slides: int) -> None:
    """Section banner shown above the slide cards of that section."""
    n_slides = len(section["slide_numbers"])
    html = (
        f'<div class="qa-section-divider" id="qa-section-{section["start"]}">'
        f'<span class="qa-section-divider-num">Slides {section["start"]}–{section["end"]}</span>'
        f'<span class="qa-section-divider-name">{_escape_html(section["name"])}</span>'
        f'<span class="qa-section-divider-meta">{n_slides} de {total_slides}</span>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def overview_panel(overview: dict, sev_counts: dict[str, int], total: int) -> None:
    """Promoted deck-level overview: storyline, filename alignment, cross-slide issues, footer consistency."""
    blocks: list[str] = []

    storyline_coh = overview.get("storyline_coherent")
    if storyline_coh is True:
        story_value = '<strong style="color: #047857;">✓ Sí</strong> · ' + _escape_html(overview.get("storyline_notes", ""))
    elif storyline_coh is False:
        story_value = '<strong style="color: #b91c1c;">✗ No</strong> · ' + _escape_html(overview.get("storyline_notes", ""))
    elif overview.get("storyline_notes"):
        story_value = _escape_html(overview["storyline_notes"])
    else:
        story_value = '<span style="color: var(--text-muted);">No evaluado (requiere modo full)</span>'

    blocks.append(
        '<div class="qa-overview-block">'
        '<div class="qa-overview-label">Storyline cross-slide</div>'
        f'<div class="qa-overview-value">{story_value}</div>'
        '</div>'
    )

    filename_align = overview.get("filename_subtitle_alignment", "—")
    blocks.append(
        '<div class="qa-overview-block">'
        '<div class="qa-overview-label">Filename ↔ títulos</div>'
        f'<div class="qa-overview-value">{_escape_html(filename_align)}</div>'
        '</div>'
    )

    footer_consistency = overview.get("footer_text_consistency_detail", {}) or {}
    if footer_consistency.get("applicable"):
        cov = footer_consistency.get("coverage_pct", 0)
        if footer_consistency.get("ok"):
            footer_value = f'<strong style="color: #047857;">✓ Consistente</strong> · {int(cov*100)}% cobertura'
        else:
            footer_value = f'<strong style="color: #b91c1c;">✗ Inconsistente</strong> · {int(cov*100)}% cobertura'
    else:
        footer_value = '<span style="color: var(--text-muted);">No aplica (deck sin pie de página)</span>'
    blocks.append(
        '<div class="qa-overview-block">'
        '<div class="qa-overview-label">Pie de página · consistencia</div>'
        f'<div class="qa-overview-value">{footer_value}</div>'
        '</div>'
    )

    caps_detail = overview.get("footer_caps_detail", {}) or {}
    if caps_detail.get("applicable"):
        caps_value = (
            '<strong style="color: #047857;">✓ Mayúsculas consistentes</strong>'
            if caps_detail.get("ok")
            else f'<strong style="color: #b45309;">✗ {len(caps_detail.get("outliers", []))} slides outlier</strong>'
        )
    else:
        caps_value = '<span style="color: var(--text-muted);">No aplica</span>'
    blocks.append(
        '<div class="qa-overview-block">'
        '<div class="qa-overview-label">Mayúsculas en pie</div>'
        f'<div class="qa-overview-value">{caps_value}</div>'
        '</div>'
    )

    cross = overview.get("cross_slide_issues") or []
    if cross:
        items = []
        for issue in cross:
            slides_str = ", ".join(str(s) for s in issue["slide_numbers"])
            items.append(
                f'<li class="qa-overview-issue">'
                f'<span class="qa-overview-issue-slides">Slides {slides_str}</span>'
                f'{_escape_html(issue["issue"])}'
                '</li>'
            )
        blocks.append(
            '<div class="qa-overview-block" style="grid-column: 1 / -1;">'
            f'<div class="qa-overview-label">Issues cross-slide · {len(cross)}</div>'
            f'<ul class="qa-overview-issues">{"".join(items)}</ul>'
            '</div>'
        )

    skipped = overview.get("skipped_slides") or []
    counts_value = (
        f'<strong>{total}</strong> slides · '
        f'{sev_counts.get("critical", 0)} critical · '
        f'{sev_counts.get("warning", 0)} warning · '
        f'{sev_counts.get("nit", 0)} nit · '
        f'{sev_counts.get("ok", 0)} OK'
        + (f' · {len(skipped)} skipped' if skipped else '')
    )
    header = (
        '<div class="qa-overview-header">'
        '<span class="qa-overview-title">Análisis general del deck</span>'
        f'<span class="qa-overview-value" style="font-size: 0.82rem; color: var(--text-muted);">{counts_value}</span>'
        '</div>'
    )

    html = f'<div class="qa-overview">{header}{"".join(blocks)}</div>'
    st.markdown(html, unsafe_allow_html=True)


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


_SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning":  "🟡",
    "nit":      "🔵",
    "ok":       "🟢",
}


def _icon_for(value) -> tuple[str, str]:
    """Map a True/False/None value to (icon, variant) for a checklist row."""
    if value is True:
        return ("✓", "ok")
    if value is False:
        return ("✗", "fail")
    return ("—", "na")


def _checklist_row_html(
    icon: str,
    variant: str,
    label: str,
    status: str,
    *,
    current: str | None = None,
    suggestion: str | None = None,
) -> str:
    current_html = (
        f'<div class="qa-checklist-current">{_escape_html(current)}</div>'
        if current else ""
    )
    suggestion_html = (
        f'<div class="qa-checklist-suggestion">{_escape_html(suggestion)}</div>'
        if suggestion else ""
    )
    return (
        '<div class="qa-checklist-item">'
        f'<div class="qa-checklist-icon {variant}">{icon}</div>'
        '<div class="qa-checklist-main">'
        '<div class="qa-checklist-row1">'
        f'<span class="qa-checklist-label">{_escape_html(label)}</span>'
        f'<span class="qa-checklist-status">{_escape_html(status)}</span>'
        '</div>'
        f'{current_html}'
        f'{suggestion_html}'
        '</div>'
        '</div>'
    )


def slide_card_html(slide: dict, thumb_bytes: bytes | None = None) -> str:
    """Build the full HTML for one slide card (header + thumbnail + checklist).

    Renders a self-contained card per slide showing all checks reviewed as a
    compact checklist with inline suggestions.
    """
    import base64 as _base64
    n = slide["slide_number"]
    score = slide.get("score")
    sev = slide.get("severity") or "nit"
    role = slide.get("role", "?")
    skipped_tag = " · skipped" if slide.get("_skipped") else ""
    title = slide["action_title"].get("current_title") or ""
    if not title:
        title = "(sin título)"
    title_disp = (title[:80] + "…") if len(title) > 80 else title

    sev_emoji = _SEVERITY_EMOJI.get(sev, "·")
    score_text = f"{score}/10" if score is not None else "—"

    # Thumbnail
    thumb_html = ""
    if thumb_bytes:
        b64 = _base64.b64encode(thumb_bytes).decode("ascii")
        thumb_html = (
            '<div class="qa-slide-thumb">'
            f'<img src="data:image/png;base64,{b64}" alt="Slide {n}" />'
            '</div>'
        )

    # ───── Compact skipped card ─────
    # When the slide is structurally skipped (cover/index/divider/closing/
    # confidentiality/references/credentials/cv/minimal) we render a much
    # tighter card with a single clear banner instead of the full checklist
    # with "Saltada (role=X)" on every row.
    _SKIPPED_ROLE_MESSAGES = {
        "cover":           ("Carátula",                 "Slide de portada — no se evalúa."),
        "index":           ("Índice / Agenda",          "Slide de índice — no se evalúa."),
        "divider":         ("Separador de sección",     "Asumido como separador de sección — no se evalúa."),
        "closing":         ("Slide de cierre",          "Slide de cierre (gracias / contacto / Q&A) — no se evalúa."),
        "confidentiality": ("Aviso de confidencialidad","Slide legal / confidencialidad — no se evalúa."),
        "references":      ("Referencias",              "Slide de referencias / clientes — no se evalúa."),
        "credentials":     ("Credenciales",             "Slide de credenciales — no se evalúa."),
        "cv":              ("CV del equipo",            "CV / perfil de consultor — no se evalúa."),
        "minimal":         ("Slide mínima",             "Slide con muy poco contenido — no se evalúa."),
    }
    if slide.get("_skipped") and role in _SKIPPED_ROLE_MESSAGES:
        role_label, message = _SKIPPED_ROLE_MESSAGES[role]
        return (
            f'<div class="qa-slide-card sev-{sev} skipped-card" id="qa-slide-{n}">'
            '<div class="qa-slide-header">'
            f'<span class="qa-slide-sev">{sev_emoji}</span>'
            f'<span class="qa-slide-num">Slide {n}</span>'
            f'<span class="qa-slide-score sev-{sev}">{score_text}</span>'
            f'<span class="qa-slide-role">{_escape_html(role)}</span>'
            f'<span class="qa-slide-title">{_escape_html(title_disp)}</span>'
            '</div>'
            '<div class="qa-slide-body">'
            f'{thumb_html}'
            '<div class="qa-slide-checks">'
            '<div class="qa-skipped-banner">'
            f'<div class="qa-skipped-banner-label">{_escape_html(role_label)}</div>'
            f'<div class="qa-skipped-banner-msg">{_escape_html(message)}</div>'
            '</div>'
            '</div>'
            '</div>'
            '</div>'
        )

    # Checklist rows — ONLY items that need improvement. OK checks are hidden
    # to reduce noise; the user wants actionable feedback, not a green roll-call.
    rows: list[str] = []

    # Action title (only if explicitly NOT an action title)
    at = slide["action_title"]
    if at.get("is_action_title") is False:
        rows.append(_checklist_row_html(
            "✗", "fail", "Action title",
            at.get("notes", "—"),
            current=at.get("current_title"),
            suggestion=at.get("suggestion"),
        ))

    # So-what (only if explicitly missing)
    sw = slide["so_what"]
    if sw.get("present") is False:
        rows.append(_checklist_row_html(
            "✗", "fail", "So-what",
            sw.get("notes", "—"),
            suggestion=sw.get("suggestion"),
        ))

    # Causa → consecuencia (only if inverted)
    cc = slide["cause_consequence"]
    if cc.get("ok") is False:
        rows.append(_checklist_row_html(
            "✗", "fail", "Causa → consecuencia",
            cc.get("notes", "—"),
        ))

    # Longitud de párrafos (only if there are long paragraphs)
    tl = slide["text_length"]
    if tl.get("ok") is False:
        status_text = tl.get("notes", "—")
        if tl.get("long_paragraphs"):
            first = tl["long_paragraphs"][0]
            more = (
                f" (+{len(tl['long_paragraphs']) - 1} más)"
                if len(tl["long_paragraphs"]) > 1 else ""
            )
            status_text = status_text + " · " + first + more
        rows.append(_checklist_row_html(
            "✗", "fail", "Longitud de párrafos",
            status_text,
            suggestion=tl.get("suggestion"),
        ))

    # Pie de página (only when footer is missing/wrong/misaligned, NOT exempt)
    footer = slide["footer"]
    exempt = footer.get("exempt")
    align_outlier = footer.get("alignment_outlier")
    footer_has_issue = (
        not exempt
        and (
            (not footer.get("present"))
            or footer.get("matches_canonical") is False
            or footer.get("aligned") is False
        )
    )
    if footer_has_issue:
        if not footer.get("present"):
            f_icon, f_variant = "—", "na"
            f_status = "Sin pie de página"
        elif footer.get("matches_canonical") is False:
            f_icon, f_variant = "✗", "fail"
            f_status = "Texto distinto al canónico"
        elif footer.get("aligned") is False and align_outlier:
            f_icon, f_variant = "✗", "fail"
            f_status = "Posición fuera del canónico del deck · " + " / ".join(
                align_outlier.get("issues", [])
            )
        else:
            f_icon, f_variant = "✗", "fail"
            f_status = "Posición fuera del canónico del deck"
        canonical = footer.get("canonical_text")
        footer_suggestion = None
        if not footer.get("present") and canonical:
            footer_suggestion = f'Agregar el footer canónico: "{canonical}"'
        elif footer.get("matches_canonical") is False and canonical:
            footer_suggestion = f'Reemplazar por el canónico: "{canonical}"'
        elif align_outlier:
            c_top = align_outlier.get("canonical_top_in")
            c_left = align_outlier.get("canonical_left_in")
            target = []
            if c_top is not None:
                target.append(f"top {c_top:.2f}″")
            if c_left is not None:
                target.append(f"left {c_left:.2f}″")
            coords = " · ".join(target) if target else "la posición canónica"
            footer_suggestion = (
                f"Mové el footer a la esquina inferior izquierda — {coords} "
                "(mediana de los pies del deck) o copiá el footer de un slide "
                "ya alineado."
            )
        rows.append(_checklist_row_html(
            f_icon, f_variant, "Pie de página",
            f_status,
            current=footer.get("current_footer") if footer.get("present") else None,
            suggestion=footer_suggestion,
        ))

    # Tamaño mínimo de fuente (only if violation)
    mfs = slide.get("min_font_size") or {}
    if mfs.get("applicable") and mfs.get("ok") is False:
        rows.append(_checklist_row_html(
            "✗", "fail",
            f"Tamaño mínimo de fuente (≥{int(mfs.get('min_required_pt', 9))}pt)",
            mfs.get("notes", "—"),
            suggestion=mfs.get("suggestion"),
        ))

    # Densidad de texto
    td = slide.get("text_density") or {}
    if td.get("applicable") and not td.get("ok"):
        rows.append(_checklist_row_html(
            "✗", "fail", "Densidad de texto",
            td.get("notes", "—"),
            suggestion=td.get("suggestion"),
        ))

    # Fuente brand (ForFuture Sans) — only if off-brand
    ff = slide.get("font_family") or {}
    if ff.get("applicable") and ff.get("ok") is False:
        rows.append(_checklist_row_html(
            "✗", "fail", "Fuente brand (ForFuture Sans)",
            ff.get("notes", "—"),
            suggestion=ff.get("suggestion"),
        ))

    # Casing — flag titles in ALL CAPS or Title Case
    tc = slide.get("title_case") or {}
    if tc.get("applicable") and not tc.get("ok"):
        violation = tc.get("case_violation")
        row_label = (
            "Título en MAYÚSCULAS" if violation == "all_caps"
            else "Título en Title Case" if violation == "title_case"
            else "Casing del título"
        )
        rows.append(_checklist_row_html(
            "✗", "fail", row_label,
            tc.get("notes", "—"),
            current=tc.get("title"),
            suggestion=tc.get("suggestion"),
        ))

    # Visual (only failing aspects)
    if slide.get("visual"):
        v = slide["visual"]
        vq = v.get("visual_quality", {})
        if vq.get("ok") is False:
            rows.append(_checklist_row_html(
                "✗", "fail", "Análisis visual",
                vq.get("notes", "—"),
                suggestion=vq.get("suggestion"),
            ))
        cr = v.get("chart_readability", {})
        if cr.get("present") and cr.get("ok") is False:
            rows.append(_checklist_row_html(
                "✗", "fail", "Chart readability",
                cr.get("notes", "—"),
                suggestion=cr.get("suggestion"),
            ))
        if v.get("design_issues"):
            issues_text = " · ".join(v["design_issues"][:3])
            if len(v["design_issues"]) > 3:
                issues_text += f" (+{len(v['design_issues']) - 3} más)"
            rows.append(_checklist_row_html(
                "✗", "fail", "Issues de diseño",
                issues_text,
            ))

    # If nothing failed, replace the checklist with a clean "all green" banner
    # so the user immediately knows the slide is approved.
    if rows:
        checks_html = '<div class="qa-checklist">' + "".join(rows) + '</div>'
    else:
        checks_html = (
            '<div class="qa-slide-allgreen">'
            '<span class="qa-slide-allgreen-icon">✓</span>'
            '<div class="qa-slide-allgreen-body">'
            '<div class="qa-slide-allgreen-title">Sin issues — slide aprobada por Holmes</div>'
            '<div class="qa-slide-allgreen-sub">Todos los checks pasaron (action title, so-what, footer, fuente, casing, densidad…).</div>'
            '</div>'
            '</div>'
        )

    return (
        f'<div class="qa-slide-card sev-{sev}" id="qa-slide-{n}">'
        '<div class="qa-slide-header">'
        f'<span class="qa-slide-sev">{sev_emoji}</span>'
        f'<span class="qa-slide-num">Slide {n}</span>'
        f'<span class="qa-slide-score sev-{sev}">{score_text}</span>'
        f'<span class="qa-slide-role">{_escape_html(role)}{_escape_html(skipped_tag)}</span>'
        f'<span class="qa-slide-title">{_escape_html(title_disp)}</span>'
        '</div>'
        '<div class="qa-slide-body">'
        f'{thumb_html}'
        f'<div class="qa-slide-checks">{checks_html}</div>'
        '</div>'
        '</div>'
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
