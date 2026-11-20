"""Leidt het Octopus-logo af van het Yuki-connectorlogo: alleen de tekstregel (y≈436-449) wordt vervangen.

Poppins Regular ±19 px, kleur (0,19,51), letterafstand ±1,6 px, achtergrond (252,252,252). Het 128px-icoon blijft ongewijzigd.
Gebruik: python scripts/build_logo.py PAD/NAAR/yuki-logo.png [PAD/NAAR/Poppins-Regular.ttf]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TEXT, SIZE, COLOR, BG, SPACING = "Octopus API Connector", 19, (0, 19, 51), (252, 252, 252), 1.6
BAND = (428, 458)          # te wissen band rond de oude tekstregel (436-449)
CAP_TOP = 435              # bovenkant van de hoofdletters in het origineel


def main(src: Path, font_path: Path) -> None:
    im = Image.open(src).convert("RGB")
    w, _ = im.size
    d = ImageDraw.Draw(im)
    d.rectangle((0, BAND[0], w, BAND[1]), fill=BG)
    font = ImageFont.truetype(str(font_path), SIZE)
    widths = [font.getlength(ch) for ch in TEXT]
    total = sum(widths) + SPACING * (len(TEXT) - 1)
    top_off = font.getbbox("O")[1]
    x = (w - total) / 2
    y = CAP_TOP - top_off
    big = Image.new("RGB", (w * 4, 60 * 4), BG)          # 4x supersampling voor zachte randen met letterafstand
    bd = ImageDraw.Draw(big)
    bf = ImageFont.truetype(str(font_path), SIZE * 4)
    bx = x * 4
    for ch, cw in zip(TEXT, widths):
        bd.text((bx, (y - (CAP_TOP - 10)) * 4), ch, font=bf, fill=COLOR)
        bx += (cw + SPACING) * 4
    strip = big.resize((w, 60), Image.LANCZOS)
    im.paste(strip.crop((0, BAND[0] - (CAP_TOP - 10), w, BAND[1] - (CAP_TOP - 10) + 1)), (0, BAND[0]))
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    im.save(out / "logo.png", optimize=True)
    print("assets/logo.png geschreven", im.size)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2] if len(sys.argv) > 2 else "/usr/share/fonts/truetype/sand-box/google/Poppins/Poppins-Regular.ttf"))
