from __future__ import annotations

import subprocess
from pathlib import Path


def run_powershell(script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), *args],
        check=False,
        capture_output=True,
        text=True,
    )

