#!/usr/bin/env bash
# Report Blender and overlay frame counts, endpoints, and sequence gaps.
#
# Usage: scripts/count_frames.sh <name> [expected]
# Blender frames are frame0001.png… and overlay frames are 000000.png….
set -euo pipefail

NAME="${1:?usage: scripts/count_frames.sh <name> [expected]}"
EXPECTED="${2:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$ROOT/renders/$NAME"
if [ -d "$PROJECT/blender-frames" ] || [ -d "$PROJECT/motion-canvas" ]; then
    BLENDER_DIR="$PROJECT/blender-frames"
    OVERLAY_DIR="$PROJECT/motion-canvas"
else
    RENDERS="$ROOT/my-animation/renders"
    BLENDER_DIR="$RENDERS/$NAME-blender"
    OVERLAY_DIR="$RENDERS/$NAME-overlay"
    if [ ! -d "$OVERLAY_DIR" ] && [ -d "$RENDERS/$NAME" ]; then
        OVERLAY_DIR="$RENDERS/$NAME"
    fi
fi

python3 - "$BLENDER_DIR" "$OVERLAY_DIR" "$EXPECTED" <<'PY'
import sys
from pathlib import Path

blender_dir, overlay_dir, expected = sys.argv[1:]
jobs = (
    ("blender", Path(blender_dir), "frame{:04d}.png", 1),
    ("overlay", Path(overlay_dir), "{:06d}.png", 0),
)
failed = False
for label, folder, pattern, start in jobs:
    files = sorted(p.name for p in folder.glob("*.png")) if folder.is_dir() else []
    if label == "blender":
        files = [name for name in files if name.startswith("frame")]
    count = len(files)
    if not files:
        print(f"{label}: 0  (missing {folder.name})")
        failed = True
        continue
    gaps = []
    for index in range(count):
        wanted = pattern.format(start + index)
        if wanted not in files:
            gaps.append(wanted)
            if len(gaps) == 5:
                break
    gap_text = "none" if not gaps else ", ".join(gaps) + (" …" if len(gaps) == 5 else "")
    print(f"{label}: {count}  {files[0]} … {files[-1]}  gaps: {gap_text}")
    if gaps:
        failed = True
    if expected and count != int(expected):
        failed = True

if expected:
    print(f"expected: {expected}  {'ok' if not failed else 'MISMATCH'}")
sys.exit(1 if failed else 0)
PY
