#!/usr/bin/env python3
"""Copy a finished Motion Canvas PNG sequence into its project render folder.

Usage:
  python3 scripts/collect_overlay.py <name> [--source PATH] [--frames N] [--replace]

The default source is my-animation/renders/<name>-overlay. If that folder does
not exist, my-animation/renders/<name> is also checked for projects created by
hand. The destination is renders/<name>/motion-canvas.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

from render_utils import validate_sequence


ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="kebab-case project name")
    parser.add_argument("--source", type=Path, help="Motion Canvas export directory")
    parser.add_argument("--frames", type=int, help="expected frame count")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace only numbered PNGs already in the destination",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.name) is None:
        raise ValueError("name must be a lowercase kebab-case project slug")
    if args.source is not None:
        source = args.source if args.source.is_absolute() else ROOT / args.source
    else:
        candidates = [
            ROOT / "my-animation" / "renders" / f"{args.name}-overlay",
            ROOT / "my-animation" / "renders" / args.name,
        ]
        populated = [path for path in candidates if path.is_dir() and any(path.glob("*.png"))]
        if len(populated) != 1:
            choices = ", ".join(str(path.relative_to(ROOT)) for path in populated) or "none"
            raise ValueError(
                f"could not select one Motion Canvas export directory (found: {choices}); "
                "pass --source explicitly"
            )
        source = populated[0]

    frames, width, height = validate_sequence(
        source,
        label="Motion Canvas",
        pattern=r"(\d{6})\.png",
        start=0,
        frames=args.frames,
        require_rgba=True,
    )
    if (width, height) != (args.width, args.height):
        raise ValueError(
            f"overlay is {width}x{height}; expected {args.width}x{args.height}"
        )

    destination = ROOT / "renders" / args.name / "motion-canvas"
    destination.mkdir(parents=True, exist_ok=True)
    existing_pngs = list(destination.glob("*.png"))
    unexpected_existing = [path.name for path in existing_pngs if re.fullmatch(r"\d{6}\.png", path.name) is None]
    if unexpected_existing:
        raise ValueError(
            f"unexpected PNGs in destination: {', '.join(unexpected_existing[:5])}; "
            "move them out before collecting a numbered sequence"
        )
    if existing_pngs and not args.replace:
        raise FileExistsError(
            f"destination already contains PNGs: {destination}; "
            "use --replace only when you intend to replace that sequence"
        )

    copied = 0
    with tempfile.TemporaryDirectory(prefix=f".{args.name}-overlay-", dir=destination.parent) as temp:
        staging = Path(temp)
        for index in range(frames):
            shutil.copy2(source / f"{index:06d}.png", staging / f"{index:06d}.png")
            copied += 1
        validate_sequence(
            staging,
            label="staged Motion Canvas",
            pattern=r"(\d{6})\.png",
            start=0,
            frames=frames,
            require_rgba=True,
        )
        if args.replace:
            for path in existing_pngs:
                if re.fullmatch(r"\d{6}\.png", path.name):
                    path.unlink()
        for index in range(frames):
            (staging / f"{index:06d}.png").replace(destination / f"{index:06d}.png")
    validate_sequence(
        destination,
        label="collected Motion Canvas",
        pattern=r"(\d{6})\.png",
        start=0,
        frames=frames,
        require_rgba=True,
    )

    print(f"collected {copied} RGBA frames to {destination.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
