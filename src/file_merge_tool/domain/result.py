from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MergeResult:
    output_paths: tuple[Path, ...]
    item_count: int
    skipped_count: int = 0
    excluded_count: int = 0
    error_skipped_count: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)
