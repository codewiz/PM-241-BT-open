#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Bernie Innocenti <bernie@codewiz.org>
"""Print an image on a TSPL thermal label printer (e.g. PM-241-BT) without
the proprietary driver.

Usage:
  uv run --with pillow python tspl-print.py IMAGE [options] > /dev/usb/lp0
  uv run --with pillow python tspl-print.py IMAGE -o /dev/usb/lp0

The printer is 203 dpi (8 dots/mm). The image is scaled to fit the label,
centered, and dithered to 1-bit.
"""

import argparse
import sys

from PIL import Image, ImageOps

DPMM = 8  # 203 dpi ~= 8 dots/mm


def image_to_tspl(img, width_mm, height_mm, gap_mm, density, speed, copies):
    wdots = width_mm * DPMM
    hdots = height_mm * DPMM
    # Scale to fit, preserving aspect ratio; center on the label.
    img = ImageOps.exif_transpose(img).convert("L")
    scale = min(wdots / img.width, hdots / img.height)
    img = img.resize((max(1, round(img.width * scale)),
                      max(1, round(img.height * scale))))
    img = img.convert("1")  # Floyd-Steinberg dither to 1-bit
    canvas = Image.new("1", (wdots, hdots), 1)  # 1 = white
    canvas.paste(img, ((wdots - img.width) // 2, (hdots - img.height) // 2))

    # TSPL BITMAP: 1 bit per dot, 0 = black. PIL mode "1" packs rows
    # MSB-first with 1 = white, which is exactly TSPL's convention.
    row_bytes = (wdots + 7) // 8
    bitmap = canvas.tobytes()
    assert len(bitmap) == row_bytes * hdots

    out = bytearray()
    out += f"SIZE {width_mm} mm,{height_mm} mm\r\n".encode()
    out += f"GAP {gap_mm} mm,0 mm\r\n".encode()
    out += f"DENSITY {density}\r\n".encode()
    out += f"SPEED {speed}\r\n".encode()
    out += b"DIRECTION 0,0\r\n"
    out += b"CLS\r\n"
    out += f"BITMAP 0,0,{row_bytes},{hdots},0,".encode() + bitmap + b"\r\n"
    out += f"PRINT {copies},1\r\n".encode()
    return bytes(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("image")
    p.add_argument("-W", "--width", type=int, default=100,
                   help="label width in mm (default 100)")
    p.add_argument("-H", "--height", type=int, default=150,
                   help="label height in mm (default 150)")
    p.add_argument("-g", "--gap", type=int, default=3,
                   help="gap between labels in mm (default 3)")
    p.add_argument("-d", "--density", type=int, default=8,
                   help="print darkness 0-15 (default 8)")
    p.add_argument("-s", "--speed", type=int, default=4,
                   help="print speed 1-6 (default 4)")
    p.add_argument("-c", "--copies", type=int, default=1)
    p.add_argument("-o", "--output", default="-",
                   help="output device/file (default stdout)")
    args = p.parse_args()

    data = image_to_tspl(Image.open(args.image), args.width, args.height,
                         args.gap, args.density, args.speed, args.copies)
    if args.output == "-":
        sys.stdout.buffer.write(data)
    else:
        with open(args.output, "wb") as f:
            f.write(data)


if __name__ == "__main__":
    main()
