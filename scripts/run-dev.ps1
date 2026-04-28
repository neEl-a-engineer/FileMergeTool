param(
    [string]$ListenHost,
    [string]$ListenPort,
    [switch]$ReplaceExisting
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = & (Join-Path $ProjectRoot "scripts\ensure-venv.ps1")
$PythonDir = Split-Path -Parent $Python
$Uvicorn = Join-Path $PythonDir "uvicorn.exe"

$HostName = if ($ListenHost) { $ListenHost } elseif ($env:FILE_MERGE_HOST) { $env:FILE_MERGE_HOST } else { "127.0.0.1" }
$Port = if ($ListenPort) { $ListenPort } elseif ($env:FILE_MERGE_PORT) { $env:FILE_MERGE_PORT } else { "8750" }
$AppMarker = "file_merge_tool.api.main:app"

function Find-ProjectServerProcesses {
    param([string]$ListenPortValue)
    $needle = "--port $ListenPortValue"
    @(
        Get-CimInstance Win32_Process |
            Where-Object {
                $cmd = $_.CommandLine
                $cmd -and $cmd -like "*$AppMarker*" -and $cmd -like "*$needle*"
            } |
            Select-Object ProcessId, ParentProcessId, CommandLine
    )
}

function Find-ListeningPids {
    param([string]$ListenPortValue)
    $pattern = ":{0}\s+.*LISTENING\s+(\d+)$" -f $ListenPortValue
    @(
        netstat -ano |
            Select-String $pattern |
            ForEach-Object {
                if ($_.Matches.Count -gt 0) {
                    [int]$_.Matches[0].Groups[1].Value
                }
            } |
            Select-Object -Unique
    )
}

function Stop-ProjectServerProcesses {
    param([string]$ListenPortValue)
    foreach ($processInfo in @(Find-ProjectServerProcesses -ListenPortValue $ListenPortValue)) {
        try {
            & taskkill.exe /PID $processInfo.ProcessId /T /F *> $null
        } catch {
            # Best effort only.
        }
    }
}

$existingProjectProcesses = @(Find-ProjectServerProcesses -ListenPortValue $Port)
if ($existingProjectProcesses.Count -gt 0) {
    if (-not $ReplaceExisting) {
        Write-Host "File Merge Tool server is already running on http://$HostName`:$Port"
        Write-Host "Use .\\40_scripts\\restart-dev.ps1 or the in-app restart button if you want to replace it."
        exit 0
    }
    Stop-ProjectServerProcesses -ListenPortValue $Port
    Start-Sleep -Seconds 2
}

$listenerPids = @(Find-ListeningPids -ListenPortValue $Port)
$projectPidSet = [System.Collections.Generic.HashSet[int]]::new()
foreach ($processInfo in @(Find-ProjectServerProcesses -ListenPortValue $Port)) {
    [void]$projectPidSet.Add([int]$processInfo.ProcessId)
}
$unexpectedPids = @($listenerPids | Where-Object { -not $projectPidSet.Contains([int]$_) })
if ($unexpectedPids.Count -gt 0) {
    $pidList = $unexpectedPids -join ", "
    throw "Port $Port is already in use by another process ($pidList). Stop it first or choose another port."
}

if (Test-Path $Uvicorn) {
    & $Uvicorn file_merge_tool.api.main:app --host $HostName --port $Port --reload
} else {
    & $Python -m uvicorn file_merge_tool.api.main:app --host $HostName --port $Port --reload
}

