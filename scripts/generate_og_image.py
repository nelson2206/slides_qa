"""Generate the Open Graph preview image for social shares.

Produces a 1200x630 PNG at static/og-image.png. Run this whenever you change
brand colors / copy. Uses Pillow which is already a project dependency.

    python scripts/generate_og_image.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


W, H = 1200, 630
OUT = Path(__file__).parent.parent / "static" / "og-image.png"
OUT.parent.mkdir(parents=True, exist_ok=True)


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


def main() -> None:
    base = _linear_gradient((W, H), BG_TOP, BG_BOTTOM)
    canvas = base.convert("RGBA")

    # Atmospheric glows
    canvas = Image.alpha_composite(
        canvas,
        _radial_glow((W, H), int(W * 0.78), int(H * 0.22), 380, 280, ACCENT, 145)
    )
    canvas = Image.alpha_composite(
        canvas,
        _radial_glow((W, H), int(W * 0.22), int(H * 0.78), 320, 240, ACCENT_PURPLE, 110)
    )
    canvas = Image.alpha_composite(
        canvas,
        _radial_glow((W, H), int(W * 0.50), int(H * 1.05), 460, 280, ACCENT_BLUE, 95)
    )

    # Subtle dot pattern
    canvas = Image.alpha_composite(canvas, _dot_pattern((W, H)))

    draw = ImageDraw.Draw(canvas)

    # Eyebrow (with pink dot)
    eyebrow_font = _load_font(24, bold=True)
    eyebrow_y = 175
    eyebrow_x = 100
    draw.ellipse([eyebrow_x, eyebrow_y + 10, eyebrow_x + 14, eyebrow_y + 24], fill=ACCENT)
    draw.text((eyebrow_x + 26, eyebrow_y + 4), "EL DETECTIVE DE TUS DECKS",
              font=eyebrow_font, fill=ACCENT)

    # Title
    title_font = _load_font(140, bold=True)
    draw.text((100, 220), "Holmes", font=title_font, fill=WHITE)

    # Subtitle
    subtitle_font = _load_font(34)
    draw.text((100, 390), "Auditoría MBB para tus decks de consultoría",
              font=subtitle_font, fill=(235, 230, 230))

    # Chips at the bottom — draw on a separate RGBA layer so the semi-
    # transparent background + opaque text composite cleanly.
    chip_font = _load_font(22, bold=True)
    chip_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chip_layer)
    chips = ["Action titles", "So-what", "Storyline", "Pie de página", "Análisis visual"]
    x = 100
    y = 478
    for label in chips:
        bbox = cd.textbbox((0, 0), label, font=chip_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        chip_w = text_w + 64
        chip_h = 46
        cd.rounded_rectangle(
            [x, y, x + chip_w, y + chip_h],
            radius=23,
            fill=(255, 255, 255, 40),
            outline=(255, 255, 255, 110),
            width=1,
        )
        # Pink dot
        dot_cx = x + 22
        dot_cy = y + chip_h // 2
        cd.ellipse(
            [dot_cx - 5, dot_cy - 5, dot_cx + 5, dot_cy + 5],
            fill=(*ACCENT, 255),
        )
        # Label — fully opaque so it composites visibly
        text_y = y + (chip_h - text_h) // 2 - 3
        cd.text((x + 38, text_y), label, font=chip_font, fill=(255, 255, 255, 255))
        x += chip_w + 12
    canvas = Image.alpha_composite(canvas, chip_layer)

    canvas.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"Saved: {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
