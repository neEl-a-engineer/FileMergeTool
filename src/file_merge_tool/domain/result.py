from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FileResult:
    relative_path: str
    source_path: str
    status: str
    classification: str | None = None
    skip_reason: str | None = None
    exception_type: str | None = None
    message: str | None = None
    details: str | None = None


@dataclass(frozen=True)
class MergeResult:
    output_paths: tuple[Path, ...]
    item_count: int
    skipped_count: int = 0
    excluded_count: int = 0
    error_skipped_count: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)
    file_results: tuple[FileResult, ...] = field(default_factory=tuple)
