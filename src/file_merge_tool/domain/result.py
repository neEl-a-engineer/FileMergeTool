from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FileResult:
    relative_path: str
    source_path: str
    status: str
    source_target_path: str | None = None
    source_target_kind: str | None = None
    classification: str | None = None
    skip_reason: str | None = None
    exception_type: str | None = None
    message: str | None = None
    details: str | None = None
    recovery: dict[str, Any] | None = None


@dataclass(frozen=True)
class MergeResult:
    output_paths: tuple[Path, ...]
    item_count: int
    skipped_count: int = 0
    excluded_count: int = 0
    error_skipped_count: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)
    file_results: tuple[FileResult, ...] = field(default_factory=tuple)
