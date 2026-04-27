from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from file_merge_tool.infrastructure.office_com.excel import read_excel_info


EXCEL_EXTENSIONS = frozenset(
    {
        ".csv",
        ".ods",
        ".tsv",
        ".xls",
        ".xlsb",
        ".xlsm",
        ".xlsx",
        ".xlt",
        ".xltm",
        ".xltx",
    }
)


@dataclass(frozen=True)
class ExtractedExcel:
    sheet_count: int
    first_sheet_text: str
    sheets: list[dict[str, object]]


def is_excel_file(path: Path) -> bool:
    return path.suffix.lower() in EXCEL_EXTENSIONS


def extract_excel_file(path: Path) -> ExtractedExcel:
    info = read_excel_info(path)
    return ExtractedExcel(
        sheet_count=info["sheet_count"],
        first_sheet_text=info["first_sheet_text"],
        sheets=info["sheets"],
    )
