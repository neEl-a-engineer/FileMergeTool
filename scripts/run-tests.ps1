$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = & (Join-Path $ProjectRoot "scripts\ensure-venv.ps1")

$env:PYTHONPATH = Join-Path $ProjectRoot "src"
Push-Location $ProjectRoot
try {
    & $Python -m pytest -q 30_tests
}
finally {
    Pop-Location
}

