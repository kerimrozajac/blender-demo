#!/usr/bin/env python3
"""Copy a Blender scene script and set its render constants.

Usage: python3 scripts/new_scene.py <name> [width] [height] [fps] [seconds] [source.py]

Default source is blender/template_scene.py. Pass another blender/*.py when its
camera, material, or animation is closer to the new shot. Writes blender/<name>.py
and does not overwrite an existing file. FRAME_END becomes seconds * fps.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if len(sys.argv) < 2:
    sys.exit("usage: python3 scripts/new_scene.py <name> [width] [height] [fps] [seconds] [source.py]")

name = sys.argv[1]
width = int(sys.argv[2]) if len(sys.argv) > 2 else 640
height = int(sys.argv[3]) if len(sys.argv) > 3 else 480
fps = int(sys.argv[4]) if len(sys.argv) > 4 else 24
seconds = float(sys.argv[5]) if len(sys.argv) > 5 else 4
source = Path(sys.argv[6]) if len(sys.argv) > 6 else ROOT / "blender" / "template_scene.py"
if not source.is_absolute():
    source = ROOT / source
dest = ROOT / "blender" / f"{name}.py"
frame_end = int(round(seconds * fps))

if dest.exists():
    sys.exit(f"exists, skipped: {dest.relative_to(ROOT)}")
if not source.is_file():
    sys.exit(f"missing source: {source}")

text = source.read_text()
values = {
    "NAME": f'"{name}"',
    "WIDTH": str(width),
    "HEIGHT": str(height),
    "FPS": str(fps),
    "FRAME_END": str(frame_end),
}
for key, value in values.items():
    updated, count = re.subn(rf"^{key}\s*=\s*.*$", f"{key} = {value}", text, count=1, flags=re.M)
    if count != 1:
        sys.exit(f"{source.name} has no {key} assignment")
    text = updated

dest.write_text(text)
print(f"created: {dest.relative_to(ROOT)} from {source.relative_to(ROOT)}")
print(f"{width}x{height}, {fps} fps, {seconds:g}s, {frame_end} frames")
print(f"rewrite build_scene(), then render:")
print(f"  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python blender/{name}.py")
