from __future__ import annotations

from datetime import datetime
from pathlib import Path


def modified_at_iso(path: Path) -> str | None:
    try:
        timestamp = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")

