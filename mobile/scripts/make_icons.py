"""Draws the app icon, Android adaptive layers, splash mark and favicon.

Run from mobile/:  ../backend/.venv/bin/python scripts/make_icons.py
Brand colours live in BRAND below (keep in sync with src/theme/tokens.ts).
"""

from pathlib import Path

from PIL import Image, ImageDraw

BRAND = {"green": "#0F7A4A", "saffron": "#F59E0B", "white": "#FFFFFF"}
OUT = Path(__file__).resolve().parent.parent / "assets" / "images"
SIZE = 1024
SCALE = 4  # draw large, then downsample for smooth edges


def basket(size: int, body: str, accent: str | None, bg: str | None, glyph_ratio: float) -> Image.Image:
    """A shopping basket with a fruit: the store mark. glyph_ratio = share of the canvas the mark spans."""
    s = size * SCALE
    img = Image.new("RGBA", (s, s), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    g = s * glyph_ratio
    ox, oy = (s - g) / 2, (s - g) / 2 + g * 0.06
    u = g / 100  # glyph units

    def p(x: float, y: float) -> tuple[float, float]:
        return ox + x * u, oy + y * u

    # Handle (its ends hide behind the rim)
    d.arc([*p(26, 6), *p(74, 62)], start=180, end=360, fill=body, width=round(7 * u))
    # Fruit peeking out of the basket (freshness), drawn before the rim so the rim overlaps it
    if accent:
        d.ellipse([*p(60, 14), *p(84, 38)], fill=accent)
    # Rim
    d.rounded_rectangle([*p(4, 30), *p(96, 44)], radius=7 * u, fill=body)
    # Body (trapezoid)
    d.polygon([p(10, 44), p(90, 44), p(80, 92), p(20, 92)], fill=body)
    d.rounded_rectangle([*p(19, 84), *p(81, 94)], radius=5 * u, fill=body)
    # Slats cut out of the body
    cut = bg or (0, 0, 0, 0)
    for x in (34, 50, 66):
        d.rounded_rectangle([*p(x - 3, 52), *p(x + 3, 82)], radius=3 * u, fill=cut)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g, s, w = BRAND["green"], BRAND["saffron"], BRAND["white"]
    basket(SIZE, w, s, g, 0.62).convert("RGB").save(OUT / "icon.png")
    # Android adaptive icon: the system masks to a circle/squircle; keep the mark inside the 66% safe zone.
    basket(SIZE, w, s, None, 0.46).save(OUT / "android-icon-foreground.png")
    Image.new("RGB", (SIZE, SIZE), g).save(OUT / "android-icon-background.png")
    basket(SIZE, w, None, None, 0.46).save(OUT / "android-icon-monochrome.png")
    basket(SIZE, w, s, None, 0.9).save(OUT / "splash-icon.png")
    basket(48, w, s, g, 0.7).convert("RGB").save(OUT / "favicon.png")
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
