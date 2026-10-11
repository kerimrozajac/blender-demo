#!/usr/bin/env bash
# Poll a render folder until it has the expected PNG count and the count stays put.
#
# Usage: scripts/wait_frames.sh <name> <frames> [overlay|blender] [stable_seconds]
# Timeout with WAIT_TIMEOUT (default 180). Exits immediately when the count is
# already higher than expected, which usually means stale frames were left behind.
set -euo pipefail

NAME="${1:?usage: scripts/wait_frames.sh <name> <frames> [overlay|blender] [stable_seconds]}"
FRAMES="${2:?usage: scripts/wait_frames.sh <name> <frames> [overlay|blender] [stable_seconds]}"
WHICH="${3:-overlay}"
STABLE_FOR="${4:-2}"
TIMEOUT="${WAIT_TIMEOUT:-180}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$ROOT/renders/$NAME"
case "$WHICH" in
  overlay)
    if [ -d "$ROOT/my-animation/renders/$NAME-overlay" ]; then
      DIR="$ROOT/my-animation/renders/$NAME-overlay"
    elif [ -d "$ROOT/my-animation/renders/$NAME" ]; then
      DIR="$ROOT/my-animation/renders/$NAME"
    elif [ -d "$PROJECT/motion-canvas" ]; then
      DIR="$PROJECT/motion-canvas"
    else
      DIR="$ROOT/my-animation/renders/$NAME-overlay"
    fi
    PATTERN='*.png'
    ;;
  blender)
    if [ -d "$PROJECT/blender-frames" ]; then
      DIR="$PROJECT/blender-frames"
    else
      DIR="$ROOT/my-animation/renders/$NAME-blender"
    fi
    PATTERN='frame*.png'
    ;;
  *) echo "which must be overlay or blender" >&2; exit 1 ;;
esac

mkdir -p "$DIR"
START=$SECONDS
PREV=-1
STABLE=0
while true; do
  COUNT="$(find "$DIR" -maxdepth 1 -name "$PATTERN" | wc -l | tr -d ' ')"
  ELAPSED=$((SECONDS - START))
  echo "t=${ELAPSED}s ${WHICH}: ${COUNT}/${FRAMES}"
  if [ "$COUNT" -gt "$FRAMES" ]; then
    echo "too many ${WHICH} frames; clear the folder before rendering again" >&2
    exit 1
  fi
  if [ "$COUNT" = "$FRAMES" ] && [ "$COUNT" = "$PREV" ]; then
    STABLE=$((STABLE + 1))
  else
    STABLE=0
  fi
  PREV="$COUNT"
  if [ "$STABLE" -ge "$STABLE_FOR" ]; then
    echo "${WHICH} ready: $COUNT"
    exit 0
  fi
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "timed out at ${COUNT}/${FRAMES}" >&2
    exit 1
  fi
  sleep 1
done
