#!/usr/bin/env python3
"""Crop a transparent logo and optionally recolor a source-pixel region in Blender.

Example:
  Blender --background --factory-startup --python scripts/prepare_logo_texture.py -- \
    --input assets/logo.png --output assets/prepared/logo.png \
    --alpha-threshold 0.31 --recolor-box 645 205 1213 355 --recolor '#E9BE72'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "blender"))

from logo_decal_utils import create_print_texture  # noqa: E402


def workspace_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source PNG logo")
    parser.add_argument("--output", required=True, help="Cropped output PNG")
    parser.add_argument("--alpha-threshold", type=float, default=0.31)
    parser.add_argument("--alpha-feather", type=float, default=0.66)
    parser.add_argument("--padding", type=int, default=3)
    parser.add_argument(
        "--recolor-box",
        nargs=4,
        type=int,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Optional artwork region in original image pixel coordinates",
    )
    parser.add_argument("--recolor", default="#E9BE72", help="RGB hex color for recolor-box")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])

    image = create_print_texture(
        workspace_path(args.input),
        workspace_path(args.output),
        alpha_threshold=args.alpha_threshold,
        alpha_feather=args.alpha_feather,
        crop_padding=args.padding,
        recolor_box=tuple(args.recolor_box) if args.recolor_box else None,
        recolor=args.recolor,
    )
    print(
        f"Prepared {args.output}: {image.size[0]}x{image.size[1]} RGBA "
        f"(alpha threshold {args.alpha_threshold:g})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
