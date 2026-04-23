$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = & (Join-Path $ProjectRoot "scripts\ensure-venv.ps1")

$env:PYTHONPATH = Join-Path $ProjectRoot "src"
& $Python -m pytest -q

