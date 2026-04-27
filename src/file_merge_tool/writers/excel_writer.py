from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.infrastructure.office_com.excel import create_excel_merge


def write_excel_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
    cell_mode: str = "formula",
) -> Path:
    return create_excel_merge(path, header_lines=header_lines, sources=sources, cell_mode=cell_mode)
