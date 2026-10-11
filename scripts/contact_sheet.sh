#!/usr/bin/env bash
# Build a small visual review sheet from selected, zero-based MP4 frame numbers.
# Usage: scripts/contact_sheet.sh <video.mp4> <frame> [frame ...]
set -euo pipefail

VIDEO="${1:?usage: scripts/contact_sheet.sh <video.mp4> <frame> [frame ...]}"
shift
[ "$#" -gt 0 ] || { echo "give at least one zero-based frame number" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$VIDEO" in /*) ;; *) VIDEO="$ROOT/$VIDEO" ;; esac
[[ -f "$VIDEO" ]] || { echo "video not found: $VIDEO" >&2; exit 1; }
for FRAME in "$@"; do
  [[ "$FRAME" =~ ^[0-9]+$ ]] || { echo "not a frame number: $FRAME" >&2; exit 1; }
done

FFMPEG="$(command -v ffmpeg || true)"
if [ -z "$FFMPEG" ]; then
  for CANDIDATE in "$ROOT"/my-animation/node_modules/@ffmpeg-installer/*/ffmpeg; do
    if [ -x "$CANDIDATE" ]; then FFMPEG="$CANDIDATE"; break; fi
  done
fi
[ -n "$FFMPEG" ] || { echo "ffmpeg not found" >&2; exit 1; }

STEM="$(basename "$VIDEO" .mp4)"
OUT_DIR="$(dirname "$VIDEO")/review-frames"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/$STEM-contact-sheet.jpg"
EXPRESSION=""
for FRAME in "$@"; do
  [ -z "$EXPRESSION" ] || EXPRESSION+="+"
  EXPRESSION+="eq(n\\,$FRAME)"
done
COLUMNS=3
ROWS=$((($# + COLUMNS - 1) / COLUMNS))
"$FFMPEG" -hide_banner -y -v error -i "$VIDEO" \
  -vf "select='$EXPRESSION',scale=320:-2,tile=${COLUMNS}x${ROWS}" \
  -fps_mode vfr -frames:v 1 -update 1 "$OUT"
echo "$OUT"
