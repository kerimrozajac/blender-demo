#!/usr/bin/env bash
# Delete overlay PNGs before a rerender so a short export cannot look complete.
#
# Usage: scripts/clear_overlay.sh <name>
# Clears the Motion Canvas export source, not the collected canonical master.
set -euo pipefail

NAME="${1:?usage: scripts/clear_overlay.sh <name>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "$ROOT/my-animation/renders/$NAME-overlay" ]; then
    DIR="$ROOT/my-animation/renders/$NAME-overlay"
elif [ -d "$ROOT/my-animation/renders/$NAME" ]; then
    DIR="$ROOT/my-animation/renders/$NAME"
else
    DIR="$ROOT/my-animation/renders/$NAME-overlay"
fi

mkdir -p "$DIR"
COUNT="$(find "$DIR" -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')"
find "$DIR" -maxdepth 1 -name '*.png' -delete
echo "removed $COUNT pngs from ${DIR#"$ROOT"/}"
