#!/usr/bin/env bash
# Extract stills from a finished mp4 so specific beats can be glanced at.
#
# Usage: scripts/grab_frames.sh <mp4> [fps] <frame:label | seconds s:label>...
# Frame numbers are zero-based, matching Motion Canvas. A seconds spec such as
# 1.8s is converted with the given fps (default 24). Stills go to
# /tmp/<mp4-stem>-check/<label>.png.
#
# Example:
#   scripts/grab_frames.sh renders/think-make-move/think-make-move.mp4 24 \
#     0:first 1.8s:phrase2 3.6s:phrase3 5.4s:hold
set -euo pipefail

MP4="${1:?usage: scripts/grab_frames.sh <mp4> [fps] <spec>...}"
shift
FPS=24
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
  FPS="$1"
  shift
fi
[ "$#" -gt 0 ] || { echo "give at least one frame:label or seconds:label spec" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$MP4" in
  /*) ;;
  *) MP4="$ROOT/$MP4" ;;
esac
FFMPEG="$(ls "$ROOT"/my-animation/node_modules/@ffmpeg-installer/*/ffmpeg | head -1)"
STEM="$(basename "$MP4" .mp4)"
OUT="/tmp/${STEM}-check"
mkdir -p "$OUT"

for SPEC in "$@"; do
  TOKEN="${SPEC%%:*}"
  LABEL="${SPEC#*:}"
  [ "$TOKEN" != "$SPEC" ] && [ -n "$LABEL" ] || { echo "bad spec: $SPEC" >&2; exit 1; }
  if [[ "$TOKEN" =~ ^[0-9]+(\.[0-9]+)?s$ ]]; then
    FRAME="$(python3 - "$TOKEN" "$FPS" <<'PY'
import sys
token, fps = sys.argv[1:]
print(int(round(float(token[:-1]) * int(fps))))
PY
)"
  elif [[ "$TOKEN" =~ ^[0-9]+$ ]]; then
    FRAME="$TOKEN"
  else
    echo "bad spec: $SPEC" >&2
    exit 1
  fi
  "$FFMPEG" -y -v error -i "$MP4" -vf "select=eq(n\\,$FRAME)" -frames:v 1 "$OUT/$LABEL.png"
  echo "$OUT/$LABEL.png  (frame $FRAME)"
done
