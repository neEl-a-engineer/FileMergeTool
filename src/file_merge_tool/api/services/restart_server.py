from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

def schedule_server_restart() -> dict[str, object]:
    host = os.getenv("FILE_MERGE_HOST", "127.0.0.1")
    port = int(os.getenv("FILE_MERGE_PORT", "8750"))
    current_pid = os.getpid()
    _launch_restart_helper(current_pid=current_pid, host=host, port=port)
    return {
        "status": "scheduled",
        "host": host,
        "port": port,
        "pid": current_pid,
    }


def _launch_restart_helper(*, current_pid: int, host: str, port: int) -> None:
    project_root = Path(__file__).resolve().parents[4]
    restart_script = project_root / "40_scripts" / "restart-dev.ps1"
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    shell_path = shutil.which("pwsh.exe") or shutil.which("powershell.exe") or "powershell.exe"
    with open(os.devnull, "wb") as sink:
        subprocess.Popen(
            [
                shell_path,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(restart_script),
                "-ProjectRoot",
                str(project_root),
                "-HostName",
                host,
                "-Port",
                str(port),
                "-CurrentPid",
                str(current_pid),
            ],
            cwd=project_root,
            stdout=sink,
            stderr=sink,
            creationflags=creationflags,
        )
