param(
    [switch]$WithOffice,
    [switch]$SkipDev
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvRoot = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment at $VenvRoot"
    python -m venv $VenvRoot
}

$InstallSpec = "."
$Extras = New-Object System.Collections.Generic.List[string]
if (-not $SkipDev) {
    $Extras.Add("dev")
}
if ($WithOffice) {
    $Extras.Add("office")
}

if ($Extras.Count -gt 0) {
    $InstallSpec = ".[" + ($Extras -join ",") + "]"
}

Write-Host "Upgrading pip"
& $VenvPython -m pip install --upgrade pip

Write-Host "Installing $InstallSpec"
& $VenvPython -m pip install -e $InstallSpec

& (Join-Path $PSScriptRoot "install-git-hooks.ps1") -ProjectRoot $ProjectRoot -SkipIfNotGitRepo

Write-Host ""
Write-Host "Setup complete."
Write-Host "Python: $VenvPython"
Write-Host "Run dev server: .\scripts\run-dev.ps1"
Write-Host "Run tests: .\scripts\run-tests.ps1"
Write-Host "Git hooks: .\.githooks (installed via core.hooksPath)"

