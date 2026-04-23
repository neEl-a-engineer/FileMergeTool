$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = & (Join-Path $ProjectRoot "scripts\ensure-venv.ps1")

$env:PYTHONPATH = Join-Path $ProjectRoot "src"
$HostName = if ($env:FILE_MERGE_HOST) { $env:FILE_MERGE_HOST } else { "127.0.0.1" }
$Port = if ($env:FILE_MERGE_PORT) { $env:FILE_MERGE_PORT } else { "8750" }

& $Python -m uvicorn file_merge_tool.api.main:app --host $HostName --port $Port --reload

