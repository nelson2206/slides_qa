"""Generate the Open Graph preview images for social shares.

Produces:
  - og-image.png        — 1200x630 landscape (standard OG, FB / LinkedIn / Slack / Telegram)
  - og-image-square.png — 1200x1200 square   (preferred by WhatsApp's preview thumbnail)

Both are rendered at 2× supersampling and then downscaled with Lanczos for
retina-sharp crispness. Run after any brand/copy change:

    python scripts/generate_og_image.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


# Render at 2x then downscale → crisper text + smoother gradients
SCALE = 2
W, H = 1200, 630          # final landscape dimensions
SQ = 1200                  # final square dimensions

ROOT = Path(__file__).parent.parent
# Write to both locations:
#  - static/ → served by Streamlit Cloud at /app/static/og-image.png
#  - docs/   → served by GitHub Pages (needed for WhatsApp OG previews
#               because Streamlit puts OG meta in <body>, not <head>)
OUT_DIRS = [ROOT / "static", ROOT / "docs"]
for d in OUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)


# ----- Brand palette -----
BG_TOP = (20, 4, 10)        # near-black burgundy
BG_BOTTOM = (61, 13, 26)    # base burgundy
ACCENT = (233, 78, 119)     # accent pink
ACCENT_PURPLE = (108, 55, 168)
ACCENT_BLUE = (20, 90, 150)
WHITE = (255, 255, 255)
WHITE_MUTED = (255, 255, 255, 210)


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try a few common fonts; fall back to Pillow default."""
    candidates_bold = [
        "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
        "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    candidates_regular = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for path in (candidates_bold if bold else candidates_regular):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _linear_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    """Vertical linear gradient."""
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _radial_glow(size: tuple[int, int], cx: int, cy: int, rx: int, ry: int, color: tuple[int, int, int], alpha: int) -> Image.Image:
    """Soft radial glow centered at (cx, cy)."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                 fill=(color[0], color[1], color[2], alpha))
    return layer.filter(ImageFilter.GaussianBlur(80))


def _dot_pattern(size: tuple[int, int], spacing: int = 18, dot_r: float = 1.1) -> Image.Image:
    """Subtle dot grid overlay."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    w, h = size
    for y in range(spacing // 2, h, spacing):
        for x in range(spacing // 2, w, spacing):
            draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r],
                         fill=(255, 255, 255, 38))
    # Fade edges with a mask
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([0, 0, w, h], fill=0)
    for i in range(40):
        a = int(255 * (i / 40))
        md.rectangle([w * 0.18 + i * 4, h * 0.10 + i * 2,
                      w * 0.82 - i * 4, h * 0.90 - i * 2], fill=a)
    masked = Image.new("RGBA", size, (0, 0, 0, 0))
    masked.paste(layer, (0, 0), mask)
    return masked


def _magnifier(layer: Image.Image, cx: int, cy: int, r: int, stroke: int) -> None:
    """Draw a Holmes-style magnifier ring + handle on the given RGBA layer."""
    d = ImageDraw.Draw(layer)
    # Ring (white, semi-translucent so glows show through)
    d.ellipse([cx - r, cy - r, cx + r, cy + r],
              outline=(255, 255, 255, 220), width=stroke)
    # Inner highlight for depth
    inner = max(2, int(stroke * 0.5))
    d.ellipse([cx - r + stroke + 2, cy - r + stroke + 2,
               cx + r - stroke - 2, cy + r - stroke - 2],
              outline=(255, 255, 255, 60), width=inner)
    # Handle (thick rounded line at 45°)
    hx1, hy1 = cx + int(r * 0.72), cy + int(r * 0.72)
    hx2, hy2 = cx + int(r * 1.55), cy + int(r * 1.55)
    d.line([(hx1, hy1), (hx2, hy2)], fill=(255, 255, 255, 220), width=stroke + 2)
    # Cap on the handle end
    cap_r = (stroke + 2) // 2
    d.ellipse([hx2 - cap_r, hy2 - cap_r, hx2 + cap_r, hy2 + cap_r],
              fill=(255, 255, 255, 220))


def _build_layout(
    size: tuple[int, int],
    *,
    eyebrow: str,
    title: str,
    subtitle: str,
    chips: list[str],
    title_size: int,
    subtitle_size: int,
    eyebrow_size: int,
    chip_size: int,
    padding: int,
    title_y: int,
    chip_y: int,
    magnifier_cx: int,
    magnifier_cy: int,
    magnifier_r: int,
    show_chips: bool = True,
) -> Image.Image:
    """Compose one layout (used for both landscape and square)."""
    w, h = size

    # 1) Base burgundy gradient
    canvas = _linear_gradient(size, BG_TOP, BG_BOTTOM).convert("RGBA")

    # 2) Atmospheric radial glows (warm pink + purple + cool blue) — richer mix
    glows = [
        (int(w * 0.78), int(h * 0.22), int(w * 0.42), int(h * 0.55), ACCENT,        165),
        (int(w * 0.22), int(h * 0.78), int(w * 0.38), int(h * 0.50), ACCENT_PURPLE, 125),
        (int(w * 0.50), int(h * 1.05), int(w * 0.55), int(h * 0.50), ACCENT_BLUE,   105),
        (int(w * 0.08), int(h * 0.10), int(w * 0.18), int(h * 0.25), (255, 200, 130),  60),
    ]
    for gx, gy, rx, ry, color, alpha in glows:
        canvas = Image.alpha_composite(canvas, _radial_glow(size, gx, gy, rx, ry, color, alpha))

    # 3) Dot pattern overlay (denser at 2× for crispness)
    canvas = Image.alpha_composite(canvas, _dot_pattern(size, spacing=22, dot_r=1.6))

    # 4) Holmes magnifier — large, soft, set into the bottom-right negative space
    fg = Image.new("RGBA", size, (0, 0, 0, 0))
    _magnifier(fg, magnifier_cx, magnifier_cy, magnifier_r,
               stroke=max(6, magnifier_r // 22))
    # Subtle bloom behind the magnifier
    bloom = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(bloom).ellipse(
        [magnifier_cx - magnifier_r - 30, magnifier_cy - magnifier_r - 30,
         magnifier_cx + magnifier_r + 30, magnifier_cy + magnifier_r + 30],
        fill=(*ACCENT, 70),
    )
    bloom = bloom.filter(ImageFilter.GaussianBlur(60))
    canvas = Image.alpha_composite(canvas, bloom)
    canvas = Image.alpha_composite(canvas, fg)

    # 5) Text layer
    text_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    td = ImageDraw.Draw(text_layer)

    # Eyebrow with pink dot
    eyebrow_font = _load_font(eyebrow_size, bold=True)
    dot_r = max(5, eyebrow_size // 5)
    eyebrow_y = padding + eyebrow_size
    td.ellipse(
        [padding, eyebrow_y - dot_r, padding + dot_r * 2, eyebrow_y + dot_r],
        fill=(*ACCENT, 255),
    )
    td.text((padding + dot_r * 2 + 14, eyebrow_y - eyebrow_size // 2 - 2),
            eyebrow, font=eyebrow_font, fill=(*ACCENT, 255))

    # Title — drop shadow first for depth, then crisp white
    title_font = _load_font(title_size, bold=True)
    shadow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow_layer).text(
        (padding + 4, title_y + 8), title, font=title_font, fill=(0, 0, 0, 150)
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(14))
    canvas = Image.alpha_composite(canvas, shadow_layer)
    td.text((padding, title_y), title, font=title_font, fill=(255, 255, 255, 255))

    # Subtitle
    subtitle_font = _load_font(subtitle_size)
    sub_y = title_y + title_size + int(title_size * 0.10)
    td.text((padding, sub_y), subtitle, font=subtitle_font, fill=(235, 230, 230, 245))

    # Chips
    if show_chips:
        chip_font = _load_font(chip_size, bold=True)
        cx = padding
        cy = chip_y
        chip_h = chip_size * 2 + 8
        for label in chips:
            bbox = td.textbbox((0, 0), label, font=chip_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            chip_w = text_w + chip_size * 3
            td.rounded_rectangle(
                [cx, cy, cx + chip_w, cy + chip_h],
                radius=chip_h // 2,
                fill=(255, 255, 255, 38),
                outline=(255, 255, 255, 130),
                width=2,
            )
            # Pink dot inside
            dx = cx + chip_size + 2
            dy = cy + chip_h // 2
            dr = max(4, chip_size // 5)
            td.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=(*ACCENT, 255))
            text_y = cy + (chip_h - text_h) // 2 - 3
            td.text((cx + chip_size + 2 + dr + 10, text_y), label,
                    font=chip_font, fill=(255, 255, 255, 255))
            cx += chip_w + chip_size // 2

    canvas = Image.alpha_composite(canvas, text_layer)
    return canvas


def _save(img: Image.Image, target_size: tuple[int, int], filenames: list[str]) -> None:
    """Downscale (Lanczos) to final size and save to every output dir."""
    final = img.resize(target_size, Image.Resampling.LANCZOS)
    rgb = final.convert("RGB")
    for d in OUT_DIRS:
        for name in filenames:
            out = d / name
            rgb.save(out, "PNG", optimize=True)
            print(f"Saved: {out}  ({out.stat().st_size // 1024} KB)")


def main() -> None:
    # ---- LANDSCAPE 1200×630 (rendered at 2400×1260) — standard OG ----
    landscape = _build_layout(
        (W * SCALE, H * SCALE),
        eyebrow="EL DETECTIVE DE TUS DECKS",
        title="Holmes",
        subtitle="Auditoría MBB para tus decks de consultoría",
        chips=["Action titles", "So-what", "Storyline", "Pie de página", "Análisis visual"],
        title_size=260,
        subtitle_size=64,
        eyebrow_size=44,
        chip_size=40,
        padding=100 * SCALE,
        title_y=400,
        chip_y=900,
        magnifier_cx=int(W * SCALE * 0.82),
        magnifier_cy=int(H * SCALE * 0.50),
        magnifier_r=int(H * SCALE * 0.30),
    )
    _save(landscape, (W, H), ["og-image.png"])

    # ---- SQUARE 1200×1200 (rendered at 2400×2400) — WhatsApp-friendly ----
    square = _build_layout(
        (SQ * SCALE, SQ * SCALE),
        eyebrow="EL DETECTIVE DE TUS DECKS",
        title="Holmes",
        subtitle="Auditoría MBB para tus decks de consultoría",
        chips=["Action titles", "So-what", "Storyline"],
        title_size=320,
        subtitle_size=70,
        eyebrow_size=48,
        chip_size=46,
        padding=120 * SCALE,
        title_y=900,
        chip_y=1900,
        magnifier_cx=int(SQ * SCALE * 0.80),
        magnifier_cy=int(SQ * SCALE * 0.28),
        magnifier_r=int(SQ * SCALE * 0.18),
    )
    _save(square, (SQ, SQ), ["og-image-square.png"])


if __name__ == "__main__":
    main()
