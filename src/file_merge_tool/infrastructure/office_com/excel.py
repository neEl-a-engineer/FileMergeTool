from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from file_merge_tool.infrastructure.office_com.office_app import require_pywin32


XL_OPEN_XML_WORKBOOK = 51


class ExcelApp:
    def __enter__(self) -> "ExcelApp":
        require_pywin32()
        import win32com.client  # type: ignore[import-not-found]

        self.app = win32com.client.DispatchEx("Excel.Application")
        self.app.Visible = False
        self.app.DisplayAlerts = False
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        quit_app = getattr(self.app, "Quit", None)
        if callable(quit_app):
            quit_app()


def read_excel_info(path: Path) -> dict[str, Any]:
    with ExcelApp() as session:
        workbook = session.app.Workbooks.Open(
            str(path.resolve()),
            ReadOnly=True,
            UpdateLinks=False,
        )
        try:
            sheet_count = int(workbook.Worksheets.Count)
            first_sheet_text = ""
            sheets: list[dict[str, Any]] = []
            if sheet_count:
                for sheet_index in range(1, sheet_count + 1):
                    worksheet = workbook.Worksheets(sheet_index)
                    formula_rows = _rows_from_matrix(_used_range_value(worksheet, "Formula"))
                    value_rows = _rows_from_matrix(_used_range_value(worksheet, "Value"))
                    if sheet_index == 1:
                        first_sheet_text = _rows_to_text(value_rows)
                    sheets.append(
                        {
                            "sheet_name": str(worksheet.Name),
                            "sheet_order": sheet_index,
                            "formula_rows": formula_rows,
                            "value_rows": value_rows,
                            "used_range": _used_range_info(formula_rows or value_rows),
                        }
                    )
            return {
                "sheet_count": sheet_count,
                "first_sheet_text": first_sheet_text,
                "sheets": sheets,
            }
        finally:
            workbook.Close(SaveChanges=False)


def create_excel_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
    cell_mode: str = "formula",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ExcelApp() as session:
        target = session.app.Workbooks.Add()
        try:
            _reset_to_single_sheet(target)
            header = target.Worksheets(1)
            header.Name = _unique_sheet_name(target, "Merge Header")
            _write_lines(header, header_lines)

            for index, source in enumerate(sources, start=1):
                separator = target.Worksheets.Add(After=target.Worksheets(target.Worksheets.Count))
                separator.Name = _unique_sheet_name(target, f"Source {index:03d}")
                _write_lines(separator, _source_lines(source))

                source_book = session.app.Workbooks.Open(
                    str(Path(source["absolute_path"]).resolve()),
                    ReadOnly=True,
                    UpdateLinks=False,
                )
                try:
                    for sheet_index in range(1, int(source_book.Worksheets.Count) + 1):
                        source_sheet = source_book.Worksheets(sheet_index)
                        source_sheet.Copy(After=target.Worksheets(target.Worksheets.Count))
                        copied = target.Worksheets(target.Worksheets.Count)
                        copied.Name = _unique_sheet_name(
                            target,
                            f"{index:03d}_{source_sheet.Name}",
                        )
                        if cell_mode == "value":
                            _freeze_sheet_values(copied)
                finally:
                    source_book.Close(SaveChanges=False)

            target.SaveAs(str(path.resolve()), FileFormat=XL_OPEN_XML_WORKBOOK)
        finally:
            target.Close(SaveChanges=False)
    return path


def _used_range_value(sheet: object, attribute: str) -> object:
    try:
        return getattr(sheet.UsedRange, attribute)
    except Exception:  # noqa: BLE001
        return None


def _rows_to_text(rows: list[list[str]]) -> str:
    flattened: list[str] = []
    for row in rows:
        for value in row:
            if value.strip():
                flattened.append(value.strip())
            if len(flattened) >= 200:
                return "\n".join(flattened)
    return "\n".join(flattened)


def _rows_from_matrix(value: object) -> list[list[str]]:
    matrix = _matrix(value)
    return [[_stringify(cell) for cell in row] for row in matrix]


def _matrix(value: object) -> list[list[object]]:
    if value is None:
        return []
    if isinstance(value, (tuple, list)):
        if not value:
            return []
        if any(isinstance(item, (tuple, list)) for item in value):
            return [
                [cell for cell in _row_values(row)]
                for row in value
            ]
        return [[item for item in value]]
    return [[value]]


def _row_values(value: object) -> list[object]:
    if isinstance(value, (tuple, list)):
        return [item for item in value]
    return [value]


def _stringify(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _used_range_info(rows: list[list[str]]) -> dict[str, int]:
    row_count = len(rows)
    column_count = max((len(row) for row in rows), default=0)
    return {
        "start_row": 1,
        "start_column": 1,
        "row_count": row_count,
        "column_count": column_count,
    }


def _flatten(value: object):
    if value is None:
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from _flatten(item)
        return
    yield value


def _freeze_sheet_values(sheet: object) -> None:
    used = sheet.UsedRange
    used.Value = used.Value


def _reset_to_single_sheet(workbook: object) -> None:
    while workbook.Worksheets.Count > 1:
        workbook.Worksheets(workbook.Worksheets.Count).Delete()


def _source_lines(source: dict[str, Any]) -> list[str]:
    return [
        "Source workbook",
        f"Relative path: {source['relative_path']}",
        f"Absolute path: {source['absolute_path']}",
        f"Modified: {source.get('modified_at') or ''}",
        f"Sheets: {source.get('sheet_count') or 0}",
    ]


def _write_lines(sheet: object, lines: list[str]) -> None:
    for row, line in enumerate(lines, start=1):
        sheet.Cells(row, 1).Value = line
    used = sheet.UsedRange
    used.Columns.AutoFit()
    sheet.Rows(1).Font.Bold = True


def _unique_sheet_name(workbook: object, desired_name: str) -> str:
    existing = {str(workbook.Worksheets(index).Name) for index in range(1, workbook.Worksheets.Count + 1)}
    base = _sanitize_sheet_name(desired_name) or "Sheet"
    if base not in existing:
        return base
    suffix = 2
    while True:
        suffix_text = f"_{suffix}"
        candidate = f"{base[: 31 - len(suffix_text)]}{suffix_text}"
        if candidate not in existing:
            return candidate
        suffix += 1


def _sanitize_sheet_name(value: str) -> str:
    sanitized = re.sub(r"[\[\]:*?/\\]", "_", value).strip("' ")
    return sanitized[:31]
