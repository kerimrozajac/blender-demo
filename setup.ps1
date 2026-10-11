# Installs everything needed on Windows (requires winget).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Gyan.FFmpeg
winget install -e --id Python.Python.3.12
winget install -e --id astral-sh.uv
winget install -e --id BlenderFoundation.Blender

Write-Host "Restart the terminal if node/npm are not found, then run:"
Push-Location my-animation
npm install
Pop-Location

uv tool install mcp-for-blender --python 3.11
Write-Host "Done. Preview overlays: cd my-animation; npm start"
Write-Host "Blender MCP addon: uvx mcp-for-blender install-addon, then enable it in Blender."
