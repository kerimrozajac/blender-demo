#!/usr/bin/env bash
# Installs everything needed on macOS (Homebrew) or Debian/Ubuntu Linux.
# Windows: run setup.ps1 instead.
set -euo pipefail
cd "$(dirname "$0")"

case "$(uname -s)" in
  Darwin)
    command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install node ffmpeg python3 uv
    [ -d /Applications/Blender.app ] || brew install --cask blender
    ;;
  Linux)
    sudo apt-get update
    sudo apt-get install -y nodejs npm ffmpeg python3 python3-venv curl
    command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
    command -v blender >/dev/null || sudo snap install blender --classic
    ;;
  *) echo "Unsupported OS; install Node 18+, ffmpeg, Python 3, uv and Blender manually." >&2; exit 1 ;;
esac

# Motion Canvas (also bundles an ffmpeg via @motion-canvas/ffmpeg)
(cd my-animation && npm install)

# Blender MCP server (optional; used by .vscode/mcp.json and .cursor/mcp.json)
uv tool install mcp-for-blender --python 3.11 || true

echo
echo "Done. Next steps:"
echo "  - Blender MCP addon: uvx mcp-for-blender install-addon, then enable it in Blender."
echo "  - Preview overlays:  cd my-animation && npm start"
[ "$(uname -s)" = Darwin ] || echo "  - Scripts reference /Applications/Blender.app/...; use your 'blender' binary instead."
