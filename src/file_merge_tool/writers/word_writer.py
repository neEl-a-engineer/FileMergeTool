from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.infrastructure.office_com.word import create_word_merge


def write_word_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
) -> Path:
    return create_word_merge(path, header_lines=header_lines, sources=sources)
