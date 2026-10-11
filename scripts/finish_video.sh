#!/usr/bin/env bash
# Backwards-compatible shell entry point; validation and compositing live in Python.
# Usage: scripts/finish_video.sh <name> <output.mp4> [fps] [frames]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?usage: scripts/finish_video.sh <name> <output.mp4> [fps] [frames]}"
OUTPUT="${2:?usage: scripts/finish_video.sh <name> <output.mp4> [fps] [frames]}"
FPS="${3:-24}"
FRAMES="${4:-}"

ARGS=("$NAME" --output "$OUTPUT" --fps "$FPS")
if [ -n "$FRAMES" ]; then
  ARGS+=(--frames "$FRAMES")
fi
exec python3 "$ROOT/scripts/finalize_video.py" "${ARGS[@]}"
