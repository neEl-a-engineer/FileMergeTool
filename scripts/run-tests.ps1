$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = & (Join-Path $ProjectRoot "scripts\ensure-venv.ps1")
$SourceRoot = if (Test-Path -LiteralPath (Join-Path $ProjectRoot "src")) {
    Join-Path $ProjectRoot "src"
} else {
    Join-Path $ProjectRoot "src"
}
$TestsRoot = if (Test-Path -LiteralPath (Join-Path $ProjectRoot "30_tests")) {
    Join-Path $ProjectRoot "30_tests"
} else {
    Join-Path $ProjectRoot "tests"
}

$env:PYTHONPATH = $SourceRoot
Push-Location $ProjectRoot
try {
    & $Python -m pytest -q $TestsRoot
}
finally {
    Pop-Location
}

