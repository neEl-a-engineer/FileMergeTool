from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from file_merge_tool.domain.file_item import ScannedItem


@dataclass(frozen=True)
class SourceTargetScan:
    requested_path: Path
    source_target_path: Path
    kind: str
    status: str
    reason: str | None = None
    items: tuple[ScannedItem, ...] = field(default_factory=tuple)
    link_target: str | None = None

    @property
    def key(self) -> str:
        return str(self.source_target_path)
