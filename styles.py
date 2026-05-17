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


def auto_scroll_to(anchor_id: str, *, delay_ms: int = 280) -> None:
    """Inject JS (via an invisible iframe) that smoothly scrolls the parent
    document to the element with `id=anchor_id`. Use sparingly — call only
    on the rerun when the target first appears, gated by st.session_state
    so it doesn't fight the user's manual scroll on subsequent reruns.
    """
    import streamlit.components.v1 as components

    # The script runs inside an iframe but reaches up to window.parent —
    # safe since the iframe is same-origin with the Streamlit app.
    components.html(
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
    import streamlit.components.v1 as components

    components.html(
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
        f'{counts_html}'
        f'{phase_html}'
        '</div>'
    )


def best_practices_html() -> str:
    """Render the MBB-style best-practices checklist for the 'Buenas prácticas' tab.

    Static content — same structure that Holmes evaluates, presented as a
    learnable checklist so the user knows what 'good' looks like before
    uploading anything.
    """
    sections = [
        {
            "label": "01 · Action titles",
            "intro": "Cada slide se sostiene sola por su título.",
            "items": [
                ("Sujeto + verbo + insight cuantificado", "'Las ventas cayeron 18% en Q3 por la pérdida de los 3 top accounts' ✓ — no 'Análisis de ventas Q3'."),
                ("Una sola idea por título", "Si necesitas 'y' o ';' para conectar dos ideas, divide en dos slides."),
                ("Test de horizontal logic", "Lee solo los titles en orden. ¿Cuentan la historia sin abrir el deck? Si no, falla."),
                ("Sin labels descriptivos", "'Contexto', 'Análisis', 'Conclusiones' son etiquetas — no titles."),
            ],
        },
        {
            "label": "02 · So-what por slide",
            "intro": "El gráfico no es el insight. La implicación sí.",
            "items": [
                ("Responde '¿y qué?'", "¿Qué decisión habilita esta slide? Si solo describe data, falta el so-what."),
                ("Takeaway arriba, evidencia abajo", "Pyramid Principle: la conclusión va primero, lo soporta abajo."),
                ("Accionable, no descriptivo", "'El cliente debe reasignar inversión a digital' ✓ — no 'El canal digital crece'."),
            ],
        },
        {
            "label": "03 · Pyramid Principle / SCQA",
            "intro": "Estructura de argumento de consultora.",
            "items": [
                ("Governing thought en la portada", "El argumento central del deck visible en slide 1 y dividers."),
                ("Argumentos MECE", "Mutually Exclusive, Collectively Exhaustive. Sin solapes, sin gaps."),
                ("Causa antes que consecuencia", "Primero evidencia, después conclusión. Nunca al revés."),
                ("SCQA en la apertura", "Situación → Complicación → Pregunta → Respuesta. Sin Complicación, no hay urgencia."),
            ],
        },
        {
            "label": "04 · Storyline (horizontal logic)",
            "intro": "El deck cuenta UNA historia, no N slides sueltos.",
            "items": [
                ("Secuencia coherente de titles", "Slide 1 → N: cada title se apoya en el anterior y prepara el siguiente."),
                ("Dividers con título de sección", "Cada chapter empieza con un divider que anuncia el argumento de la sección."),
                ("Sin slides redundantes", "Si dos slides dicen lo mismo, fusiona o elimina."),
                ("Filename refleja el deck", "El nombre del archivo debe contener keywords del governing thought."),
            ],
        },
        {
            "label": "05 · Layout y consistencia",
            "intro": "El detalle visual importa. Inconsistencias gritan junior.",
            "items": [
                ("Pie de página en la esquina inferior izquierda", "Convención de la consultora: footer alineado a la esquina inferior-izquierda. Mismo texto, misma posición (top + left), misma altura en todas las slides de contenido."),
                ("Fuente brand: ForFuture Sans", "Familia oficial de la consultora. Pesos disponibles: Light, Regular, Medium, Bold, Black (cada uno con italic). Cualquier otra familia es una rotura de brand."),
                ("Títulos en sentence case — NUNCA Title Case ni MAYÚSCULAS", "La consultora usa sentence case: solo la primera palabra y los nombres propios capitalizados. ✓ 'Las ventas cayeron 18% en Q3'. ✗ 'Las Ventas Cayeron 18% en Q3' (Title Case). ✗ 'LAS VENTAS CAYERON 18% EN Q3' (grito)."),
                ("Mayúsculas consistentes en pie y secundarios", "Footer y subtítulos: todo title case, todo sentence case — sin mezcla entre slides."),
                ("Jerarquía tipográfica clara", "Title, subtitle, body, caption — tamaños y pesos diferenciados pero consistentes."),
            ],
        },
        {
            "label": "06 · Densidad de texto",
            "intro": "Si necesitas leer el slide, es muy denso.",
            "items": [
                ("Máximo ~250 palabras por slide", "Más que eso: divide en dos o agrega un visual que resuma."),
                ("Bullets de 2-3 líneas", "Nunca párrafos de prosa en bullets. Si no entra en 3 líneas, reescríbelo."),
                ("Tamaño mínimo de fuente: 9pt", "Cualquier texto bajo 9pt es ilegible en proyector e impresión."),
                ("Si hay mucho texto, agrega visuales", "Un gráfico o esquema bien hecho reemplaza media página de prosa."),
            ],
        },
        {
            "label": "07 · Gráficos y visuales",
            "intro": "El gráfico vende el insight. Sin contexto, no vende nada.",
            "items": [
                ("Ejes con unidades visibles", "Siempre. '%', 'M USD', 'unidades' — no asumas que se entiende."),
                ("Fuente + periodo del dato", "'Fuente: SUNAT, 2020-2024' al pie del gráfico. Sin esto, es opinión."),
                ("Takeaway en el título del gráfico", "El título dice la conclusión, no describe los ejes."),
                ("Sin ruido visual", "Sin 3D, sin gradientes decorativos, sin leyendas redundantes, sin gridlines innecesarios."),
                ("Una sola comparación por gráfico", "Si contesta dos preguntas, divide en dos gráficos."),
            ],
        },
        {
            "label": "08 · Boilerplate (Holmes los ignora)",
            "intro": "Estos slides son estructurales, no llevan action title.",
            "items": [
                ("Carátula / portada", "Solo título del proyecto + cliente + fecha. Sin so-what."),
                ("Avisos de confidencialidad", "Plantilla legal. Holmes la detecta y la salta."),
                ("Índice / agenda", "Solo lista de capítulos. Holmes la detecta por título o por estructura numerada."),
                ("Dividers de sección", "Solo número + nombre del chapter. Holmes los detecta por layout o por título exacto."),
                ("Referencias / credenciales / CVs", "Material de cierre. Holmes los detecta por keywords del título."),
                ("Cierre / contacto / gracias", "Holmes los detecta y los salta."),
            ],
        },
    ]

    blocks = []
    for sec in sections:
        # Split the original 'NN · Title' label into a refined typographic
        # number + name layout.
        raw_label = sec["label"]
        if " · " in raw_label:
            num_str, name_str = raw_label.split(" · ", 1)
        else:
            num_str, name_str = "", raw_label

        items_html = "".join(
            '<li class="qa-bp-item">'
            '<span class="qa-bp-marker" aria-hidden="true"></span>'
            '<div class="qa-bp-item-body">'
            f'<div class="qa-bp-item-title">{_escape_html(title)}</div>'
            f'<div class="qa-bp-item-detail">{_escape_html(detail)}</div>'
            '</div>'
            '</li>'
            for title, detail in sec["items"]
        )
        blocks.append(
            '<section class="qa-bp-section">'
            '<header class="qa-bp-section-head">'
            f'<span class="qa-bp-section-num">{_escape_html(num_str)}</span>'
            '<div class="qa-bp-section-titles">'
            f'<h3 class="qa-bp-section-name">{_escape_html(name_str)}</h3>'
            f'<p class="qa-bp-section-intro">{_escape_html(sec["intro"])}</p>'
            '</div>'
            '</header>'
            f'<ul class="qa-bp-list">{items_html}</ul>'
            '</section>'
        )
    return (
        '<div class="qa-bp-wrapper">'
        '<div class="qa-bp-header">'
        '<div class="qa-bp-eyebrow">Holmes evalúa contra este estándar</div>'
        '<h2 class="qa-bp-title">Buenas prácticas para decks de consultoría</h2>'
        '<p class="qa-bp-sub">MECE, Pyramid Principle, SCQA, Minto — el estándar que todo Minsaiter debe conocer. Holmes audita cada slide contra esta lista.</p>'
        '</div>'
        f'{"".join(blocks)}'
        '</div>'
    )


def hide_nav() -> None:
    """Force-hide the navigator (and disconnect any active observer). Call on
    page renders where results aren't ready, so stale `qa-nav-visible` class
    from a previous session/file is cleared."""
    import streamlit.components.v1 as components
    components.html(
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

    # Checklist rows
    rows: list[str] = []

    # Action title
    at = slide["action_title"]
    icon, variant = _icon_for(at.get("is_action_title"))
    rows.append(_checklist_row_html(
        icon, variant, "Action title",
        at.get("notes", "—"),
        current=at.get("current_title") if at.get("is_action_title") is not True else None,
        suggestion=at.get("suggestion"),
    ))

    # So-what
    sw = slide["so_what"]
    icon, variant = _icon_for(sw.get("present"))
    rows.append(_checklist_row_html(
        icon, variant, "So-what",
        sw.get("notes", "—"),
        suggestion=sw.get("suggestion"),
    ))

    # Causa → consecuencia
    cc = slide["cause_consequence"]
    icon, variant = _icon_for(cc.get("ok"))
    rows.append(_checklist_row_html(
        icon, variant, "Causa → consecuencia",
        cc.get("notes", "—"),
    ))

    # Longitud de párrafos
    tl = slide["text_length"]
    icon, variant = _icon_for(tl.get("ok"))
    status_text = tl.get("notes", "—")
    if tl.get("long_paragraphs"):
        # Show first long paragraph snippet inline
        first = tl["long_paragraphs"][0]
        more = (
            f" (+{len(tl['long_paragraphs']) - 1} más)"
            if len(tl["long_paragraphs"]) > 1 else ""
        )
        status_text = status_text + " · " + first + more
    rows.append(_checklist_row_html(
        icon, variant, "Longitud de párrafos",
        status_text,
        suggestion=tl.get("suggestion"),
    ))

    # Pie de página
    footer = slide["footer"]
    exempt = footer.get("exempt")
    align_outlier = footer.get("alignment_outlier")
    if not footer.get("present"):
        if exempt:
            f_icon, f_variant = "—", "na"
            f_status = f"No aplica · slide de tipo {role}"
        else:
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
    elif footer.get("aligned") is False:
        f_icon, f_variant = "✗", "fail"
        f_status = "Posición fuera del canónico del deck"
    else:
        f_icon, f_variant = "✓", "ok"
        f_status = "Canónico OK"
    canonical = footer.get("canonical_text")
    footer_suggestion = None
    if not footer.get("present") and canonical and not exempt:
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

    # Tamaño mínimo de fuente
    mfs = slide.get("min_font_size") or {}
    if mfs.get("applicable"):
        icon, variant = _icon_for(mfs.get("ok"))
        rows.append(_checklist_row_html(
            icon, variant, f"Tamaño mínimo de fuente (≥{int(mfs.get('min_required_pt', 9))}pt)",
            mfs.get("notes", "—"),
            suggestion=mfs.get("suggestion"),
        ))

    # Densidad de texto — slide muy cargada
    td = slide.get("text_density") or {}
    if td.get("applicable") and not td.get("ok"):
        rows.append(_checklist_row_html(
            "✗", "fail", "Densidad de texto",
            td.get("notes", "—"),
            suggestion=td.get("suggestion"),
        ))

    # Fuente brand (ForFuture Sans)
    ff = slide.get("font_family") or {}
    if ff.get("applicable"):
        icon, variant = _icon_for(ff.get("ok"))
        rows.append(_checklist_row_html(
            icon, variant, "Fuente brand (ForFuture Sans)",
            ff.get("notes", "—"),
            suggestion=ff.get("suggestion"),
        ))

    # Casing — flag titles in ALL CAPS or Title Case (only sentence case OK)
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

    # Visual (if present)
    if slide.get("visual"):
        v = slide["visual"]
        vq = v.get("visual_quality", {})
        icon, variant = _icon_for(vq.get("ok"))
        rows.append(_checklist_row_html(
            icon, variant, "Análisis visual",
            vq.get("notes", "—"),
            suggestion=vq.get("suggestion"),
        ))
        cr = v.get("chart_readability", {})
        if cr.get("present"):
            icon, variant = _icon_for(cr.get("ok"))
            rows.append(_checklist_row_html(
                icon, variant, "Chart readability",
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

    checks_html = '<div class="qa-checklist">' + "".join(rows) + '</div>'

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
