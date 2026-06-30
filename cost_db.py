"""Cost-tracking database for Holmes executions.

Records one row per PPTX evaluation: project code, execution date, the browser
(or machine) ID of whoever ran it, and the cost breakdown.

Primary backend: a self-contained SQLite database (stdlib `sqlite3`, no server,
no extra dependency). One file, ACID, queryable. Exports to .xlsx on demand for
download / sharing.

Optional backend: an HTTP webhook (Power Automate / Logic Apps) — if a URL is
configured, each record is POSTed there instead of written locally. Useful to
land rows in a corporate SharePoint/OneDrive Excel.

IMPORTANT — Streamlit Cloud persistence caveat
-----------------------------------------------
Streamlit Cloud has an EPHEMERAL filesystem: a local .db is wiped on every
redeploy and is not shared between concurrent sessions. On a single machine
(local run) it persists normally. For a durable cloud DB either point
COST_DB_PATH at a persistent volume, use the webhook backend, or migrate the
small surface in this module to a hosted DB (Postgres/Turso/Supabase).
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Schema — (column name, SQLite type). Order IS the table/export layout.
# Add new fields at the END so existing databases stay compatible.
# ---------------------------------------------------------------------------

_SCHEMA: list[tuple[str, str]] = [
    ("fecha_ejecucion", "TEXT"),       # ISO local datetime, e.g. 2026-05-19 14:32:05
    ("codigo_proyecto", "TEXT"),       # user-entered project code
    ("id_navegador", "TEXT"),          # persistent browser id (or machine fallback)
    ("usuario", "TEXT"),               # optional free-text label (name / email)
    ("archivo", "TEXT"),               # deck file name
    ("modo", "TEXT"),                  # "local" | "full"
    ("proveedor", "TEXT"),             # "claude" | "openai" | "" (local)
    ("slides_total", "INTEGER"),
    ("slides_analizados", "INTEGER"),
    ("slides_skipped", "INTEGER"),
    ("score_promedio", "REAL"),
    ("costo_per_slide_usd", "REAL"),
    ("costo_storyline_usd", "REAL"),
    ("costo_visual_usd", "REAL"),
    ("costo_total_usd", "REAL"),
]

COLUMNS: list[str] = [name for name, _ in _SCHEMA]
_NUMERIC_COLS = {name for name, typ in _SCHEMA if typ in ("INTEGER", "REAL")}
_TABLE = "ejecuciones"


def default_db_path() -> Path:
    """Resolve the cost-DB path.

    Priority: COST_DB_PATH env var → ./data/cost_log.db next to this module.
    """
    env = os.environ.get("COST_DB_PATH")
    if env:
        return Path(env)
    return Path(__file__).parent / "data" / "cost_log.db"


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
      3. Fall back to a per-machine id (local runs) so the logger never blocks.
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

    fallback = session_state.get("_holmes_fallback_id")
    if not fallback:
        fallback = _machine_fallback_id()
        session_state["_holmes_fallback_id"] = fallback
    return fallback


# ---------------------------------------------------------------------------
# Optional remote backend — Power Automate / Logic Apps HTTP webhook
# ---------------------------------------------------------------------------

def webhook_url_from_env() -> str | None:
    return os.environ.get("COST_WEBHOOK_URL") or None


def post_webhook(record: dict[str, Any], webhook_url: str, timeout: float = 15.0) -> None:
    """POST a single record (JSON) to an HTTP trigger. Raises on non-2xx."""
    import requests  # local import: keep module import cheap / optional dep

    resp = requests.post(webhook_url, json=record, timeout=timeout)
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# SQLite store
# ---------------------------------------------------------------------------

def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")  # better concurrent read/write
    cols_ddl = ",\n  ".join(f'"{name}" {typ}' for name, typ in _SCHEMA)
    conn.execute(
        f'CREATE TABLE IF NOT EXISTS {_TABLE} (\n'
        f'  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  {cols_ddl}\n)'
    )
    conn.commit()
    return conn


def _coerce(col: str, value: Any) -> Any:
    """Empty strings in numeric columns become NULL; numbers stay numbers."""
    if col in _NUMERIC_COLS and (value == "" or value is None):
        return None
    return value


def append_record(
    record: dict[str, Any],
    db_path: str | Path | None = None,
    *,
    webhook_url: str | None = None,
) -> Path | None:
    """Append one execution record to the cost database.

    Backend selection:
      - If `webhook_url` (or COST_WEBHOOK_URL env) is set → POST the record to
        that flow and return None.
      - Otherwise → INSERT into the local SQLite DB and return its path.

    `record` is keyed by the names in COLUMNS; missing keys store NULL/blank,
    unknown keys are ignored.
    """
    webhook = webhook_url or webhook_url_from_env()
    if webhook:
        post_webhook(record, webhook)
        return None

    path = Path(db_path) if db_path else default_db_path()
    placeholders = ", ".join("?" for _ in COLUMNS)
    col_list = ", ".join(f'"{c}"' for c in COLUMNS)
    values = [_coerce(c, record.get(c, None)) for c in COLUMNS]

    conn = _connect(path)
    try:
        conn.execute(
            f"INSERT INTO {_TABLE} ({col_list}) VALUES ({placeholders})", values
        )
        conn.commit()
    finally:
        conn.close()
    return path


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
        "score_promedio": (round(avg_score, 2) if avg_score is not None else None),
        "costo_per_slide_usd": round(ac.get("per_slide_usd", 0.0), 6),
        "costo_storyline_usd": round(ac.get("storyline_usd", 0.0), 6),
        "costo_visual_usd": round(ac.get("visual_usd", 0.0), 6),
        "costo_total_usd": round(ac.get("total_usd", 0.0), 6),
    }


# ---------------------------------------------------------------------------
# Reads / exports
# ---------------------------------------------------------------------------

def row_count(db_path: str | Path | None = None) -> int:
    """Number of logged executions."""
    path = Path(db_path) if db_path else default_db_path()
    if not path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(path), timeout=10.0)
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {_TABLE}")
            return int(cur.fetchone()[0])
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


def fetch_rows(
    db_path: str | Path | None = None, limit: int | None = None
) -> list[dict[str, Any]]:
    """Return logged rows (newest first), each as a COLUMNS-keyed dict."""
    path = Path(db_path) if db_path else default_db_path()
    if not path.exists():
        return []
    conn = sqlite3.connect(str(path), timeout=10.0)
    try:
        col_list = ", ".join(f'"{c}"' for c in COLUMNS)
        sql = f"SELECT {col_list} FROM {_TABLE} ORDER BY id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        cur = conn.execute(sql)
        return [dict(zip(COLUMNS, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def total_cost_usd(db_path: str | Path | None = None) -> float:
    """Sum of costo_total_usd across all executions."""
    path = Path(db_path) if db_path else default_db_path()
    if not path.exists():
        return 0.0
    try:
        conn = sqlite3.connect(str(path), timeout=10.0)
        try:
            cur = conn.execute(
                f"SELECT COALESCE(SUM(costo_total_usd), 0) FROM {_TABLE}"
            )
            return float(cur.fetchone()[0] or 0.0)
        finally:
            conn.close()
    except sqlite3.Error:
        return 0.0


def export_xlsx_bytes(db_path: str | Path | None = None) -> bytes | None:
    """Export the whole DB to an .xlsx in memory for download. None if empty."""
    rows = fetch_rows(db_path)
    if not rows:
        return None
    from openpyxl import Workbook  # local import: only needed for export

    wb = Workbook()
    ws = wb.active
    ws.title = _TABLE
    ws.append(COLUMNS)
    # fetch_rows returns newest-first; export oldest-first for readability
    for r in reversed(rows):
        ws.append([r.get(c) for c in COLUMNS])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# Backwards-compatible alias (app.py previously called read_log_bytes)
def read_log_bytes(db_path: str | Path | None = None) -> bytes | None:
    return export_xlsx_bytes(db_path)
