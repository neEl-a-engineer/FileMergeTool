# File Merge Tool

Local web and CLI tool for collecting project files into AI-friendly merge
artifacts while preserving paths, timestamps, and structure.


## Highlights

- One FastAPI GUI for every merge kind
- CLI commands for automation and batch use
- Normal and sensitive outputs split by marker rules
- Server-side history with re-download support
- Windows-first Office merge with Microsoft 365 desktop apps

## Status

This repository is an early working implementation. The current slice supports:

- Recursive folder/file list export as JSON
- Text-like file merge export as JSON
- `.msg` mail merge export as JSON
- PDF merge export as `.pdf`
- Image merge export as self-contained HTML and/or PPTX
- PowerPoint, Excel, and Word merge through Microsoft Office COM automation
- Shared exclude rules for folders and file extensions
- FastAPI web server
- CLI commands for every merge kind
- PowerShell helper scripts
- Server-side preset storage
- History-backed downloads

The Office merge features are intentionally isolated behind COM adapters.
They require Microsoft 365 desktop apps on Windows. Non-Office JSON, PDF, and
image HTML features do not require Office.

## Requirements

- Windows 10/11 is the primary target
- Python 3.10+
- Microsoft 365 desktop apps are required for PowerPoint, Excel, and Word merge

## Setup On A New PC

Clone the repository and create a local virtual environment:

```powershell
git clone <your-repo-url>
cd NginxWebServer_FileMergeTool
.\scripts\setup-dev.ps1
```

If you plan to use PowerPoint, Excel, or Word merge on that machine:

```powershell
.\scripts\setup-dev.ps1 -WithOffice
```

## Quick Start

```powershell
.\scripts\run-dev.ps1
```

`run-dev.ps1`, `run-cli.ps1`, and `run-tests.ps1` automatically run
`setup-dev.ps1` if `.venv` does not exist yet.

Open:

```text
http://127.0.0.1:8750
```

## CLI Examples

```powershell
.\scripts\run-cli.ps1 file-list D:\WebServer --output-name file-list.json
.\scripts\run-cli.ps1 text-merge D:\WebServer --output-name text-merge.json --exclude-dir .git --exclude-ext .png
.\scripts\run-cli.ps1 image-merge D:\Pictures --output-stem images --format html --format pptx
.\scripts\run-cli.ps1 pdf-merge D:\Docs --output-stem merged
.\scripts\run-cli.ps1 mail-merge D:\Mail --output-stem mail-merge
.\scripts\run-cli.ps1 powerpoint-merge D:\Slides --output-stem merged
```

## Development

Run tests:

```powershell
.\scripts\run-tests.ps1
```

## Contact

- Handle: `neEl`
- Email: `neel_a_engineer@outlook.jp`

## Repository Layout

```text
src/            Application source
tests/          Automated tests and fixtures
scripts/        PowerShell helpers
.github/        GitHub workflow and templates
sample_configs/ Example request payloads
```

## GitHub Notes

Local `.venv/` and `80_workspace/` folders are intentionally gitignored in the
public bundle. Sample files must not contain private data.
