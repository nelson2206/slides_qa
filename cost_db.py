"""Cost-tracking database for Holmes executions.

Records one row per PPTX evaluation: project code, execution date, the browser
(or machine) ID of whoever ran it, and the cost breakdown.

Backend: an Excel workbook (.xlsx) via openpyxl. The path is configurable so the
same code can point at a local file (dev) or a file the user supplies.

IMPORTANT — Streamlit Cloud persistence caveat
-----------------------------------------------
Streamlit Cloud has an EPHEMERAL filesystem: a local .xlsx is wiped on every
redeploy and is not shared between concurrent sessions. For durable, multi-user
logging migrate `CostStore` to Google Sheets / a real DB (see `append_record`'s
docstring for the single swap point). On a single machine (local run) the Excel
backend persists normally.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook

# ---------------------------------------------------------------------------
# Schema — column order IS the sheet layout. Add new fields at the END so
# existing workbooks stay aligned.
# ---------------------------------------------------------------------------

COLUMNS: list[str] = [
    "fecha_ejecucion",      # ISO local datetime, e.g. 2026-05-19 14:32:05
    "codigo_proyecto",      # user-entered project code
    "id_navegador",         # persistent browser id (or machine/session fallback)
    "usuario",              # optional free-text label (name / email)
    "archivo",              # deck file name
    "modo",                 # "local" | "full"
    "proveedor",            # "claude" | "openai" | "" (local)
    "slides_total",
    "slides_analizados",
    "slides_skipped",
    "score_promedio",
    "costo_per_slide_usd",
    "costo_storyline_usd",
    "costo_visual_usd",
    "costo_total_usd",
]

_SHEET_NAME = "ejecuciones"


def default_db_path() -> Path:
    """Resolve the cost-DB path.

    Priority: COST_DB_PATH env var → ./data/cost_log.xlsx next to this module.
    """
    env = os.environ.get("COST_DB_PATH")
    if env:
        return Path(env)
    return Path(__file__).parent / "data" / "cost_log.xlsx"


# ---------------------------------------------------------------------------
# Browser / machine identity
# ---------------------------------------------------------------------------

def _machine_fallback_id() -> str:
    """Stable-ish id for local (non-web) runs: hashed MAC address.

    Useless for distinguishing users on Streamlit Cloud (all sessions share the
    server), which is exactly why the browser-localStorage id is preferred.
    """
    return f"machine-{uuid.getnode():x}"


def get_browser_id(session_state: Any) -> str:
    """Return a persistent id for the current browser, caching in session_state.

    Strategy:
      1. Reuse session_state["_holmes_browser_id"] if already resolved.
      2. Read/create a UUID in the browser's localStorage via streamlit-js-eval.
         The component returns None on its first render (then triggers a rerun);
         we persist the value the moment it arrives.
      3. Fall back to a per-machine id (local runs) or a per-session UUID so the
         logger never blocks on a missing id.
    """
    cached = session_state.get("_holmes_browser_id")
    if cached:
        return cached

    browser_id: str | None = None
    try:
        from streamlit_js_eval import streamlit_js_eval

        browser_id = streamlit_js_eval(
            js_expressions=(
                "(() => { const k='holmes_browser_id';"
                " let v=window.localStorage.getItem(k);"
                " if(!v){ v=(crypto.randomUUID?crypto.randomUUID():"
                "String(Date.now())+Math.random()); "
                "window.localStorage.setItem(k,v);} return v; })()"
            ),
            key="holmes_browser_id_probe",
        )
    except Exception:  # noqa: BLE001 — component missing or JS disabled
        browser_id = None

    if browser_id:
        session_state["_holmes_browser_id"] = browser_id
        return browser_id

    # Component hasn't answered yet (returns None on first render) or is absent.
    # Use a stable fallback so we always have *something* to log, but don't
    # cache it as the browser id so a later real value can still win.
    fallback = session_state.get("_holmes_fallback_id")
    if not fallback:
        fallback = _machine_fallback_id()
        session_state["_holmes_fallback_id"] = fallback
    return fallback


# ---------------------------------------------------------------------------
# Remote backend — Power Automate / Logic Apps HTTP webhook
# ---------------------------------------------------------------------------
#
# Writing to a corporate SharePoint/OneDrive Excel from an external web app
# (Streamlit Cloud) can't be done with just the file URL — it needs an auth
# bridge. The lowest-friction bridge in a Microsoft 365 tenant is a Power
# Automate flow with a "When an HTTP request is received" trigger that maps the
# posted JSON into an "Add a row into a table" (Excel Online) action.
#
# The app POSTs the flat `record` dict (keys = COLUMNS) as JSON to the flow URL.
# Configure the URL via the COST_WEBHOOK_URL env var or st.secrets and pass it
# through `append_record(..., webhook_url=...)`.

def webhook_url_from_env() -> str | None:
    return os.environ.get("COST_WEBHOOK_URL") or None


def post_webhook(record: dict[str, Any], webhook_url: str, timeout: float = 15.0) -> None:
    """POST a single record to a Power Automate / Logic Apps HTTP trigger.

    Raises on network error or non-2xx so the caller can surface it.
    """
    import requests  # local import: keep module import cheap / optional dep

    resp = requests.post(webhook_url, json=record, timeout=timeout)
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Excel store
# ---------------------------------------------------------------------------

def _ensure_workbook(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = _SHEET_NAME
    ws.append(COLUMNS)
    wb.save(path)


def append_record(
    record: dict[str, Any],
    db_path: str | Path | None = None,
    *,
    webhook_url: str | None = None,
) -> Path | None:
    """Append one execution record to the cost log.

    Backend selection:
      - If `webhook_url` (or COST_WEBHOOK_URL env) is set → POST the record to
        that Power Automate / Logic Apps flow, which writes the row into the
        SharePoint/OneDrive Excel. Returns None (no local path).
      - Otherwise → append to the local Excel workbook and return its path.

    `record` is keyed by the names in COLUMNS; for the local backend missing
    keys are written blank and unknown keys ignored.

    Local concurrency: load → append → save with a few retries. Good enough for
    a single machine / low write volume.
    """
    webhook = webhook_url or webhook_url_from_env()
    if webhook:
        post_webhook(record, webhook)
        return None

    path = Path(db_path) if db_path else default_db_path()
    row = [record.get(col, "") for col in COLUMNS]

    last_err: Exception | None = None
    for attempt in range(5):
        try:
            _ensure_workbook(path)
            wb = load_workbook(path)
            ws = wb[_SHEET_NAME] if _SHEET_NAME in wb.sheetnames else wb.active
            ws.append(row)
            wb.save(path)
            return path
        except (PermissionError, OSError) as exc:  # file locked / open in Excel
            last_err = exc
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(
        f"No se pudo escribir el registro de costos en {path}: {last_err}"
    )


def build_record(
    *,
    project_code: str,
    browser_id: str,
    file_name: str,
    result: dict[str, Any],
    est: dict[str, Any] | None = None,
    user_label: str = "",
    avg_score: float | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Assemble a COLUMNS-keyed record from a finished QA `result`."""
    ac = result.get("actual_cost") or {}
    overview = result.get("deck_overview") or {}
    slides = result.get("slides") or []
    skipped = len(overview.get("skipped_slides", []) or [])
    analyzed = sum(1 for s in slides if not s.get("_skipped"))
    stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "fecha_ejecucion": stamp,
        "codigo_proyecto": project_code.strip(),
        "id_navegador": browser_id,
        "usuario": (user_label or "").strip(),
        "archivo": file_name,
        "modo": result.get("mode", ""),
        "proveedor": result.get("provider", ""),
        "slides_total": len(slides),
        "slides_analizados": analyzed,
        "slides_skipped": skipped,
        "score_promedio": (round(avg_score, 2) if avg_score is not None else ""),
        "costo_per_slide_usd": round(ac.get("per_slide_usd", 0.0), 6),
        "costo_storyline_usd": round(ac.get("storyline_usd", 0.0), 6),
        "costo_visual_usd": round(ac.get("visual_usd", 0.0), 6),
        "costo_total_usd": round(ac.get("total_usd", 0.0), 6),
    }


def read_log_bytes(db_path: str | Path | None = None) -> bytes | None:
    """Return the raw .xlsx bytes for download, or None if no log exists yet."""
    path = Path(db_path) if db_path else default_db_path()
    if not path.exists():
        return None
    return path.read_bytes()


def row_count(db_path: str | Path | None = None) -> int:
    """Number of logged executions (data rows, excluding the header)."""
    path = Path(db_path) if db_path else default_db_path()
    if not path.exists():
        return 0
    try:
        wb = load_workbook(path, read_only=True)
        ws = wb[_SHEET_NAME] if _SHEET_NAME in wb.sheetnames else wb.active
        n = max(0, ws.max_row - 1)
        wb.close()
        return n
    except Exception:  # noqa: BLE001
        return 0
