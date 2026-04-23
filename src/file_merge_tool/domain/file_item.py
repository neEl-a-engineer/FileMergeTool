from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScannedItem:
    absolute_path: Path
    relative_path: str
    kind: str
    modified_at: str | None
    excluded: bool = False
    excluded_reason: str | None = None
    link_target: str | None = None
