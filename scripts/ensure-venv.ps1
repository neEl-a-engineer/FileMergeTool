$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host ".venv was not found. Running setup-dev.ps1..."
    & (Join-Path $ProjectRoot "scripts\setup-dev.ps1") | Out-Host
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment setup did not create .venv\Scripts\python.exe"
}

$VenvPython

