"""Split a logo PNG into a shield icon (top) and wordmark (bottom) transparent PNGs.

Run with Blender (it ships numpy):
  blender --background --factory-startup --python scripts/split_logo.py -- \
      "assets/SkyShield Protection Logo-1.png" assets/umbrella-rain/skyshield-shield.png \
      assets/umbrella-rain/skyshield-text.png [--cut 0.31] [--pad 8] [--min-gap 8]

The split happens at the topmost empty row band (alpha > cut) of at least --min-gap rows.
Pixels keep their original RGB; alpha below the cut (soft glow) is removed and the
remainder is remapped so antialiased edges stay smooth. The source is never modified.
"""
import sys
from pathlib import Path

import bpy
import numpy as np


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    pos = [a for a in args if not a.startswith("--")]
    opts = {a: args[i + 1] for i, a in enumerate(args) if a.startswith("--")}
    src, shield_out, text_out = (Path(p) for p in pos[:3])
    cut = float(opts.get("--cut", 0.31))
    pad = int(opts.get("--pad", 8))
    min_gap = int(opts.get("--min-gap", 8))

    image = bpy.data.images.load(str(src))
    image.colorspace_settings.name = "sRGB"
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)  # row 0 is the bottom

    alpha = px[:, :, 3]
    occupied = (alpha > cut).any(axis=1)
    rows = np.where(occupied)[0]
    lo, hi = rows.min(), rows.max()
    gaps, run, start = [], 0, 0
    for r in range(lo, hi + 1):
        if not occupied[r]:
            if run == 0:
                start = r
            run += 1
        elif run:
            gaps.append((start, run))
            run = 0
    big = [g for g in gaps if g[1] >= min_gap]
    if not big:
        raise SystemExit(f"no gap >= {min_gap} rows found; gaps: {gaps}")
    gap_start, gap_len = big[-1]  # highest gap in image rows (bottom-up)
    split = gap_start + gap_len // 2
    print("gaps:", gaps, "split row:", split)

    def extract(r0, r1, out):
        part = px[r0:r1].copy()
        a = part[:, :, 3]
        keep = a > cut
        cols = np.where(keep.any(axis=0))[0]
        rws = np.where(keep.any(axis=1))[0]
        x0, x1 = max(cols.min() - pad, 0), min(cols.max() + pad + 1, w)
        y0, y1 = max(rws.min() - pad, 0), min(rws.max() + pad + 1, part.shape[0])
        part = part[y0:y1, x0:x1]
        a = np.clip((part[:, :, 3] - cut) / (1 - cut), 0, 1)
        part[:, :, 3] = a
        part[a == 0, :3] = 0
        img = bpy.data.images.new(out.stem, part.shape[1], part.shape[0], alpha=True)
        img.colorspace_settings.name = "sRGB"
        img.alpha_mode = "STRAIGHT"
        img.pixels.foreach_set(part.reshape(-1))
        img.filepath_raw = str(out)
        img.file_format = "PNG"
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save()
        print(out, part.shape[1], "x", part.shape[0])

    extract(split, h, shield_out)
    extract(0, split, text_out)


main()
