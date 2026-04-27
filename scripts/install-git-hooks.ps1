param(
    [string]$ProjectRoot = "",
    [switch]$SkipIfNotGitRepo
)

$ErrorActionPreference = "Stop"

$ResolvedProjectRoot = if ($ProjectRoot) {
    (Resolve-Path -LiteralPath $ProjectRoot).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

$HooksPath = Join-Path $ResolvedProjectRoot ".githooks"
if (-not (Test-Path -LiteralPath $HooksPath -PathType Container)) {
    throw ".githooks directory not found at $HooksPath"
}

Push-Location $ResolvedProjectRoot
try {
    $RepoRoot = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) {
        if ($SkipIfNotGitRepo) {
            Write-Host "Git repository not found. Skipping hook installation."
            return
        }

        throw "Git repository not found under $ResolvedProjectRoot"
    }

    & git config core.hooksPath .githooks
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to set core.hooksPath to .githooks"
    }
}
finally {
    Pop-Location
}

Write-Host "Installed Git hooks from .githooks"
Write-Host "pre-push will run check-sensitive-data.ps1 -Mode push"

