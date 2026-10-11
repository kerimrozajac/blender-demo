#!/usr/bin/env python3
"""Write a speckle-noise RGBA PNG for distressed print texture (no dependencies).

Usage: python3 scripts/make_grain.py [out.png] [width] [height] [density]
Default: my-animation/src/assets/print-grain.png, 240x96, density 0.08.

In Motion Canvas, put it inside a `cache` Node above the text with
compositeOperation={'destination-out'} to knock speckles out of the letters.
"""

import random
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "my-animation/src/assets/print-grain.png"
width = int(sys.argv[2]) if len(sys.argv) > 2 else 240
height = int(sys.argv[3]) if len(sys.argv) > 3 else 96
density = float(sys.argv[4]) if len(sys.argv) > 4 else 0.08

rng = random.Random(11)
raw = bytearray()
for _ in range(height):
    raw.append(0)
    for _ in range(width):
        alpha = rng.randint(80, 210) if rng.random() < density else 0
        raw += bytes((255, 255, 255, alpha))


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
png += chunk(b"IEND", b"")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(png)
print(f"wrote {out}")
