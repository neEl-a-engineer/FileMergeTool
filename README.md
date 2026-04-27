# File Merge Tool

Local web and CLI tool for collecting project files into AI-friendly merge
artifacts while preserving paths, timestamps, and structure.

## Highlights

- One FastAPI GUI for every merge kind
- CLI commands for automation and batch use
- AI-friendly merge JSON outputs for text, Office, and PDF workflows
- Per-run summary JSON with history-backed preview and download actions
- Normal and sensitive outputs split by marker rules
- Server-side history with preview and re-download support
- Windows-first Office merge with Microsoft 365 desktop apps

## Status

This repository is an early working implementation. The current slice supports:

- Recursive folder/file list export as JSON
- Text-like file merge export as JSON
- `.msg` mail merge export as JSON
- PDF merge export as `.pdf` plus merge JSON
- Image merge export as self-contained HTML and/or PPTX
- PowerPoint merge export as `.pptx` plus merge JSON
- Excel merge export as formula/value `.xlsx` plus formula/value JSON
- Word merge export as `.docx` plus merge JSON
- Per-run summary JSON output
- Shared exclude rules for folders and file extensions
- Shared output naming and history folder structure
- FastAPI web server
- CLI commands for every merge kind
- PowerShell helper scripts
- Server-side preset storage
- History-backed preview and download actions
- Server restart action from the settings view

The Office merge features are intentionally isolated behind COM adapters.
They require Microsoft 365 desktop apps on Windows. Non-Office JSON, PDF, and
image HTML features do not require Office.

## Requirements

- Windows 10/11 is the primary target
- Python 3.10+
- Microsoft 365 desktop apps are required for PowerPoint, Excel, and Word merge

## Setup

```powershell
git clone <your-repo-url>
cd FileMergeTool
.\scripts\setup-dev.ps1
```

`setup-dev.ps1` installs the repo's `pre-push` hook through `.githooks/`, so
`git push` runs the sensitive scan automatically once the repository is cloned
normally.

If you plan to use PowerPoint, Excel, or Word merge on that machine:

```powershell
.\scripts\setup-dev.ps1 -WithOffice
```

## Quick Start

```powershell
.\scripts\run-dev.ps1
```

Open:

```text
http://127.0.0.1:8750
```

The history tab lets you reopen JSON outputs inside the app and open Office/PDF
outputs with the Windows machine's default desktop app when running locally.

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

Install git hooks:

```powershell
.\scripts\install-git-hooks.ps1
```

Run the local sensitive data scan:

```powershell
.\scripts\check-sensitive-data.ps1 -Mode push
```

Create the public bundle again after updating the project:

```powershell
.\scripts\export-public.ps1
```

## Repository Layout

```text
.githooks/       Git hook wrappers
src/             Application source
tests/           Automated tests and fixtures
scripts/         PowerShell helpers
.github/         GitHub workflow and templates
sample_configs/  Example request payloads
```

## GitHub Notes

Local `.venv/` and `80_workspace/` folders are intentionally gitignored in the
public bundle. Sample files must not contain private data.

Run `.\scripts\install-git-hooks.ps1` after cloning if you want the bundled
pre-push hook to run the sensitive scan automatically.

## Contact

- Handle: `neEl`
- Email: `neel_a_engineer@outlook.jp`
