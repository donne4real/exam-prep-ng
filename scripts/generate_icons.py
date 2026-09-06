#!/usr/bin/env python3
"""Generate the PWA install icons in public/.

Design: Nigerian-green rounded square, a white open book (the study mark),
and a gold accent bar beneath it. Drawn with Pillow primitives only so the
script runs anywhere without font or asset dependencies.

Run:  python scripts/generate_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

PUBLIC = Path(__file__).parent.parent / "public"

GREEN = (0, 135, 81, 255)  # #008751
GREEN_DARK = (0, 100, 60, 255)
WHITE = (255, 255, 255, 255)
GOLD = (255, 215, 0, 255)  # #FFD700

SIZES = {
    "pwa-192x192.png": 192,
    "pwa-512x512.png": 512,
    "apple-touch-icon.png": 180,
}


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def draw_book(draw: ImageDraw.ImageDraw, s: int) -> None:
    """Open book centered horizontally, upper-middle of the icon."""
    w = int(s * 0.56)          # total book width
    h = int(s * 0.34)          # book height
    cx, top = s // 2, int(s * 0.24)
    left, right = cx - w // 2, cx + w // 2
    bottom = top + h
    spine_x = cx
    cover = int(s * 0.045)     # page thickness

    # Outer cover (slightly larger dark green "binding")
    draw.polygon(
        [(left, top + cover), (spine_x, top), (right, top + cover),
         (right, bottom - cover), (spine_x, bottom), (left, bottom - cover)],
        fill=WHITE,
    )
    # Page split: thin green line down the spine
    draw.line([(spine_x, top + int(cover * 1.6)), (spine_x, bottom - int(cover * 1.6))],
              fill=GREEN_DARK, width=max(2, int(s * 0.02)))
    # Page lines on both leaves
    line_w = max(2, int(s * 0.014))
    for frac in (0.32, 0.52, 0.72):
        y = top + int(h * frac)
        draw.line([(left + int(w * 0.08), y), (spine_x - int(w * 0.06), y)], fill=GREEN, width=line_w)
        draw.line([(spine_x + int(w * 0.06), y), (right - int(w * 0.08), y)], fill=GREEN, width=line_w)


def draw_accent(draw: ImageDraw.ImageDraw, s: int) -> None:
    """Gold bar under the book — a nod to the flag's white stripe."""
    w, h = int(s * 0.34), int(s * 0.055)
    cx, y = s // 2, int(s * 0.70)
    rounded(draw, (cx - w // 2, y, cx + w // 2, y + h), h // 2, GOLD)


def make_icon(size: int, maskable_padding: bool = False) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * 0.22)
    rounded(draw, (0, 0, size - 1, size - 1), radius, GREEN)
    draw_book(draw, size)
    draw_accent(draw, size)
    return img


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name, size in SIZES.items():
        make_icon(size).save(PUBLIC / name)
        print(f"wrote public/{name} ({size}x{size})")


if __name__ == "__main__":
    main()
