"""Render slide thumbnails.

Three backends, in order of fidelity:

1. **PowerPoint COM** (Windows + PowerPoint installed): faithful slide images
   via `pywin32`. ~1-2s per slide. **Local dev only — NOT deployable.**

2. **LibreOffice headless** (Linux/Mac/Windows with LibreOffice + poppler):
   convert .pptx → PDF → PNG. ~10s cold start, ~0.3s per slide after.
   **The deployment-safe path.** Works on Streamlit Cloud, Docker, etc.

3. **Pillow schematic** (always available): draws bounding boxes + title text.
   Instant, no external deps. Not a faithful render but works EVERYWHERE.

No tokens consumed by any path — rendering is 100% local.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable


# Default thumbnail dimensions (16:9-ish aspect for 13.33"×7.5" decks)
THUMB_W = 480
THUMB_H = 270


def is_powerpoint_available() -> tuple[bool, str]:
    """Detect whether PowerPoint COM is usable on this machine."""
    if os.name != "nt":
        return False, "PowerPoint COM solo está disponible en Windows."
    try:
        import win32com.client  # noqa: F401
        return True, "pywin32 (PowerPoint COM)"
    except ImportError:
        pass
    try:
        import comtypes.client  # noqa: F401
        return True, "comtypes (PowerPoint COM)"
    except ImportError:
        pass
    return False, "Falta `pywin32` o `comtypes`. `pip install pywin32`."


def _libreoffice_binary() -> str | None:
    """Find soffice/libreoffice on PATH or common install locations."""
    for name in ("soffice", "libreoffice", "soffice.exe"):
        path = shutil.which(name)
        if path:
            return path
    # Common Windows install locations
    win_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    # macOS install location
    mac_paths = ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    for p in win_paths + mac_paths:
        if Path(p).exists():
            return p
    return None


def is_libreoffice_available() -> tuple[bool, str]:
    """Detect whether LibreOffice + poppler (via pdf2image) are usable."""
    binary = _libreoffice_binary()
    if not binary:
        return False, "LibreOffice no encontrado en PATH ni en ubicaciones standard."
    try:
        import pdf2image  # noqa: F401
    except ImportError:
        return False, "Falta `pdf2image`. `pip install pdf2image`."
    return True, f"LibreOffice ({binary}) + pdf2image"


def cache_key_for(pptx_path: str | Path) -> str:
    """Stable identifier per .pptx file (used as cache key)."""
    p = Path(pptx_path)
    h = hashlib.sha1()
    h.update(str(p.resolve()).encode("utf-8"))
    try:
        st = p.stat()
        h.update(str(st.st_size).encode("utf-8"))
        h.update(str(int(st.st_mtime)).encode("utf-8"))
    except OSError:
        pass
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Backend 1: PowerPoint COM
# ---------------------------------------------------------------------------

def render_via_powerpoint(
    pptx_path: str | Path,
    *,
    width: int = THUMB_W,
    height: int = THUMB_H,
    output_dir: str | Path | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> dict[int, bytes]:
    """Render all slides via PowerPoint COM. Returns {slide_number: png_bytes}.

    `progress_cb(done, total)` is called after each slide if provided.
    """
    pptx_abs = str(Path(pptx_path).resolve())
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="ppt_thumbs_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Try pywin32 first (more common)
    ppt_app = None
    try:
        import win32com.client  # type: ignore
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    except ImportError:
        import comtypes.client  # type: ignore
        ppt_app = comtypes.client.CreateObject("PowerPoint.Application")

    # PowerPoint COM is finicky about Visible — modern Office requires Visible=True
    try:
        ppt_app.Visible = True
    except Exception:
        pass

    pres = ppt_app.Presentations.Open(
        pptx_abs, WithWindow=False, ReadOnly=True
    )

    result: dict[int, bytes] = {}
    try:
        total = pres.Slides.Count
        for i in range(1, total + 1):
            slide = pres.Slides(i)
            out_path = output_dir / f"slide_{i:03d}.png"
            # Export takes: FileName, FilterName, ScaleWidth, ScaleHeight
            slide.Export(str(out_path), "PNG", width, height)
            if out_path.exists():
                result[i] = out_path.read_bytes()
            if progress_cb:
                progress_cb(i, total)
    finally:
        try:
            pres.Close()
        except Exception:
            pass
        # Don't Quit() — user may have other presentations open.
    return result


# ---------------------------------------------------------------------------
# Backend 2: LibreOffice headless (deployment-safe)
# ---------------------------------------------------------------------------

def render_via_libreoffice(
    pptx_path: str | Path,
    *,
    width: int = THUMB_W,
    height: int = THUMB_H,
    output_dir: str | Path | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> dict[int, bytes]:
    """Render all slides via LibreOffice → PDF → PNG (via pdf2image).

    Workflow:
      1. `soffice --headless --convert-to pdf ...` → PDF in temp dir.
      2. `pdf2image.convert_from_path()` → PIL images per page.
      3. Resize each to the requested thumbnail dims, encode as PNG bytes.

    Requires LibreOffice in PATH and pdf2image (which needs poppler-utils).
    """
    binary = _libreoffice_binary()
    if not binary:
        raise RuntimeError("LibreOffice no disponible.")

    try:
        from pdf2image import convert_from_path
    except ImportError as e:
        raise RuntimeError(f"pdf2image faltante: {e}")

    pptx_abs = str(Path(pptx_path).resolve())
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="ppt_thumbs_lo_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: PPTX → PDF
    cmd = [
        binary, "--headless", "--norestore", "--nofirststartwizard",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        pptx_abs,
    ]
    proc = subprocess.run(cmd, capture_output=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(
            f"LibreOffice falló: rc={proc.returncode}, stderr={proc.stderr.decode('utf-8', 'ignore')[:300]}"
        )

    pdf_path = output_dir / (Path(pptx_abs).stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"LibreOffice no produjo PDF en {pdf_path}")

    # Step 2: PDF → PNG per page
    # DPI 100 gives a usable thumbnail; we resize to THUMB_W × THUMB_H after.
    pil_images = convert_from_path(str(pdf_path), dpi=100)

    from PIL import Image
    result: dict[int, bytes] = {}
    total = len(pil_images)
    for i, img in enumerate(pil_images, start=1):
        # Preserve aspect ratio: thumbnail() resizes in-place, fits within box
        thumb = img.copy()
        thumb.thumbnail((width, height), Image.LANCZOS)
        buf = io.BytesIO()
        thumb.save(buf, format="PNG", optimize=True)
        result[i] = buf.getvalue()
        if progress_cb:
            progress_cb(i, total)
    return result


# ---------------------------------------------------------------------------
# Backend 3: Pillow schematic
# ---------------------------------------------------------------------------

_BURGUNDY = (61, 13, 26)
_ACCENT = (233, 78, 119)
_CREAM = (244, 241, 236)
_CARD = (255, 255, 255)
_BORDER = (210, 200, 195)
_TITLE_TEXT = (255, 255, 255)
_BODY_TEXT = (80, 50, 60)


def _wrap_text(text: str, max_chars_per_line: int) -> list[str]:
    """Greedy word-wrap into N lines."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for w in words:
        if current_len + len(w) + (1 if current else 0) > max_chars_per_line and current:
            lines.append(" ".join(current))
            current = [w]
            current_len = len(w)
        else:
            current.append(w)
            current_len += len(w) + (1 if current_len else 0)
    if current:
        lines.append(" ".join(current))
    return lines


def render_schematic(
    slide: dict[str, Any],
    slide_width_in: float,
    slide_height_in: float,
    *,
    width: int = THUMB_W,
    height: int = THUMB_H,
) -> bytes:
    """Generate a fast schematic preview: bounding boxes + title text."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, height), color=_CREAM)
    draw = ImageDraw.Draw(img)

    # Try to load Inter from common locations; fall back to default
    title_font = None
    body_font = None
    for size, target in [(18, "title_font"), (11, "body_font")]:
        for path in [
            "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
            "C:/Windows/Fonts/arialbd.ttf",     # Arial Bold
            "C:/Windows/Fonts/Inter-Bold.ttf",
        ]:
            try:
                font = ImageFont.truetype(path, size)
                if target == "title_font":
                    title_font = font
                else:
                    body_font = font
                break
            except (OSError, IOError):
                continue
    if title_font is None:
        title_font = ImageFont.load_default()
    if body_font is None:
        body_font = ImageFont.load_default()

    sw = max(slide_width_in or 13.333, 0.1)
    sh = max(slide_height_in or 7.5, 0.1)
    px_per_in_x = width / sw
    px_per_in_y = height / sh

    for shape in slide.get("shapes", []):
        top = shape.get("top_in")
        left = shape.get("left_in")
        w_in = shape.get("width_in")
        h_in = shape.get("height_in")
        if top is None or left is None or w_in is None or h_in is None:
            continue
        x0 = int(left * px_per_in_x)
        y0 = int(top * px_per_in_y)
        x1 = int((left + w_in) * px_per_in_x)
        y1 = int((top + h_in) * px_per_in_y)
        x0 = max(0, min(x0, width - 1))
        y0 = max(0, min(y0, height - 1))
        x1 = max(x0 + 2, min(x1, width))
        y1 = max(y0 + 2, min(y1, height))

        is_title = shape.get("is_title")
        fill = _BURGUNDY if is_title else _CARD
        outline = _BURGUNDY if is_title else _BORDER
        draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=1)

        text = (shape.get("text") or "").strip()
        if not text:
            continue
        # Truncate if too long for the box
        box_w = x1 - x0
        box_h = y1 - y0
        if is_title:
            text_color = _TITLE_TEXT
            font = title_font
            line_h = 20
            max_chars = max(8, box_w // 8)
        else:
            text_color = _BODY_TEXT
            font = body_font
            line_h = 14
            max_chars = max(8, box_w // 6)

        wrapped = _wrap_text(text, max_chars)
        max_lines = max(1, box_h // line_h)
        wrapped = wrapped[:max_lines]
        if wrapped and len(_wrap_text(text, max_chars)) > max_lines:
            wrapped[-1] = (wrapped[-1][:max(1, max_chars - 1)] + "…")
        for j, line in enumerate(wrapped):
            try:
                draw.text(
                    (x0 + 4, y0 + 4 + j * line_h),
                    line,
                    fill=text_color,
                    font=font,
                )
            except Exception:
                # ImageDraw may choke on certain glyphs with the fallback font
                draw.text((x0 + 4, y0 + 4 + j * line_h), line.encode("ascii", "ignore").decode(), fill=text_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_schematic_for_deck(
    deck: dict[str, Any],
    *,
    width: int = THUMB_W,
    height: int = THUMB_H,
    slide_numbers: list[int] | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> dict[int, bytes]:
    """Render schematics for an entire deck dict (output of extract_deck)."""
    slide_w_in = deck.get("slide_width_in") or 13.333
    slide_h_in = deck.get("slide_height_in") or 7.5
    result: dict[int, bytes] = {}
    slides = deck.get("slides", [])
    target_nums = set(slide_numbers) if slide_numbers else None
    total = len(slides)
    for i, slide in enumerate(slides, start=1):
        n = slide["slide_number"]
        if target_nums is not None and n not in target_nums:
            continue
        result[n] = render_schematic(slide, slide_w_in, slide_h_in, width=width, height=height)
        if progress_cb:
            progress_cb(i, total)
    return result


# ---------------------------------------------------------------------------
# Unified API
# ---------------------------------------------------------------------------

def render(
    *,
    pptx_path: str | Path | None = None,
    deck: dict[str, Any] | None = None,
    mode: str = "auto",
    progress_cb: Callable[[int, int], None] | None = None,
) -> tuple[dict[int, bytes], str]:
    """Render thumbnails.

    Modes:
      - "powerpoint" — Windows + Office (faithful, local dev only)
      - "libreoffice" — Linux/Mac/Windows + LibreOffice (faithful, deployable)
      - "schematic" — always works (bounding-box sketch)
      - "auto" — try libreoffice → powerpoint → schematic in that order.
        On the server, libreoffice wins; locally on Windows, powerpoint is faster.
    """
    if mode == "powerpoint":
        if pptx_path is None:
            raise ValueError("powerpoint mode requires pptx_path")
        return render_via_powerpoint(pptx_path, progress_cb=progress_cb), "powerpoint"

    if mode == "libreoffice":
        if pptx_path is None:
            raise ValueError("libreoffice mode requires pptx_path")
        return render_via_libreoffice(pptx_path, progress_cb=progress_cb), "libreoffice"

    if mode == "schematic":
        if deck is None:
            raise ValueError("schematic mode requires deck")
        return render_schematic_for_deck(deck, progress_cb=progress_cb), "schematic"

    # auto — prefer LibreOffice (cross-platform), then PowerPoint, then schematic
    if pptx_path is not None:
        lo_avail, _ = is_libreoffice_available()
        if lo_avail:
            try:
                thumbs = render_via_libreoffice(pptx_path, progress_cb=progress_cb)
                if thumbs:
                    return thumbs, "libreoffice"
            except Exception:
                pass
        pp_avail, _ = is_powerpoint_available()
        if pp_avail:
            try:
                thumbs = render_via_powerpoint(pptx_path, progress_cb=progress_cb)
                if thumbs:
                    return thumbs, "powerpoint"
            except Exception:
                pass

    if deck is not None:
        return render_schematic_for_deck(deck, progress_cb=progress_cb), "schematic"

    raise RuntimeError("No se pudo renderizar: ningún backend disponible.")
