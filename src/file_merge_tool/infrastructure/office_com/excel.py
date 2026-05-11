from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from file_merge_tool.domain.recovery import (
    MergeWriteReport,
    RecoveryInfo,
    RecoveryUnit,
    dedupe_steps,
    recovery_overview_lines,
    source_recovery_lines,
    worst_fidelity,
)
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
) -> MergeWriteReport:
    path.parent.mkdir(parents=True, exist_ok=True)
    recoveries: list[tuple[str, RecoveryInfo]] = []
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
                recovery = _merge_source_into_workbook(
                    session=session,
                    target=target,
                    source=source,
                    source_index=index,
                    cell_mode=cell_mode,
                )
                recoveries.append((str(source["absolute_path"]), recovery))
                _write_lines(separator, _source_lines(source, recovery))

            _write_lines(
                header,
                [
                    *header_lines,
                    "",
                    *recovery_overview_lines([info for _, info in recoveries]),
                ],
            )
            target.SaveAs(str(path.resolve()), FileFormat=XL_OPEN_XML_WORKBOOK)
        finally:
            target.Close(SaveChanges=False)
    return MergeWriteReport(output_path=path, recoveries=tuple(recoveries))


def _merge_source_into_workbook(
    *,
    session: ExcelApp,
    target: object,
    source: dict[str, Any],
    source_index: int,
    cell_mode: str,
) -> RecoveryInfo:
    source_book = None
    open_steps: list[str] = []
    try:
        source_book, open_steps = _open_source_book_with_retry(session, Path(source["absolute_path"]))
        unit_results = [
            _copy_or_rebuild_sheet(
                target=target,
                source_book=source_book,
                extracted_sheet=extracted_sheet,
                source_index=source_index,
                cell_mode=cell_mode,
            )
            for extracted_sheet in source.get("sheets", [])
        ]
        return _source_recovery_from_units(unit_results, tuple(open_steps))
    except Exception as exc:  # noqa: BLE001
        rebuilt_units = [
            _rebuild_sheet(
                target=target,
                extracted_sheet=extracted_sheet,
                source_index=source_index,
                cell_mode=cell_mode,
                recovery_steps=("source_open_failed", "rebuild_from_extracted_rows"),
                message=f"The workbook could not be reopened; rebuilt {extracted_sheet['sheet_name']} from extracted cells.",
                original_error=exc,
            )
            for extracted_sheet in source.get("sheets", [])
        ]
        if rebuilt_units and any(unit.status == "merged" for unit in rebuilt_units):
            return _source_recovery_from_units(
                rebuilt_units,
                dedupe_steps((*open_steps, "source_open_failed", "rebuild_from_extracted_rows")),
                fallback_message=str(exc),
            )
        return RecoveryInfo(
            status="skipped",
            fidelity="skipped",
            message=f"The workbook could not be merged after retry and rebuild attempts: {exc}",
            recovery_steps=dedupe_steps((*open_steps, "source_open_failed", "source_skipped")),
        )
    finally:
        if source_book is not None:
            source_book.Close(SaveChanges=False)


def _open_source_book_with_retry(session: ExcelApp, path: Path) -> tuple[object, list[str]]:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            workbook = session.app.Workbooks.Open(
                str(path.resolve()),
                ReadOnly=True,
                UpdateLinks=False,
            )
            return workbook, [] if attempt == 0 else ["source_open_retry_recovered"]
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    if last_error is None:
        raise RuntimeError("The workbook could not be opened.")
    raise last_error


def _copy_or_rebuild_sheet(
    *,
    target: object,
    source_book: object,
    extracted_sheet: dict[str, Any],
    source_index: int,
    cell_mode: str,
) -> RecoveryUnit:
    sheet_name = str(extracted_sheet["sheet_name"])
    last_error: Exception | None = None
    for attempt in range(2):
        copied = None
        try:
            source_sheet = source_book.Worksheets(int(extracted_sheet["sheet_order"]))
            source_sheet.Copy(After=target.Worksheets(target.Worksheets.Count))
            copied = target.Worksheets(target.Worksheets.Count)
            copied.Name = _unique_sheet_name(target, f"{source_index:03d}_{sheet_name}")
            if cell_mode == "value":
                _freeze_sheet_values(copied)
            return RecoveryUnit(
                unit_type="sheet",
                unit_name=sheet_name,
                status="merged",
                fidelity="exact" if attempt == 0 else "retry_recovered",
                message=None if attempt == 0 else f"The sheet {sheet_name} succeeded after retry.",
                recovery_steps=() if attempt == 0 else ("sheet_copy_retry_recovered",),
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if copied is not None:
                _delete_sheet(copied)
            continue

    return _rebuild_sheet(
        target=target,
        extracted_sheet=extracted_sheet,
        source_index=source_index,
        cell_mode=cell_mode,
        recovery_steps=("sheet_copy_failed", "rebuild_from_extracted_rows"),
        message=f"The sheet {sheet_name} could not be copied; rebuilt it from extracted cells.",
        original_error=last_error,
    )


def _rebuild_sheet(
    *,
    target: object,
    extracted_sheet: dict[str, Any],
    source_index: int,
    cell_mode: str,
    recovery_steps: tuple[str, ...],
    message: str,
    original_error: Exception | None = None,
) -> RecoveryUnit:
    sheet_name = str(extracted_sheet["sheet_name"])
    rebuilt = None
    try:
        rebuilt = target.Worksheets.Add(After=target.Worksheets(target.Worksheets.Count))
        rebuilt.Name = _unique_sheet_name(target, f"{source_index:03d}_{sheet_name}")
        note_lines = [
            "Recovery note",
            "Fidelity: structure_rebuilt",
            f"Message: {message}",
            f"Steps: {' -> '.join(recovery_steps)}",
        ]
        rows_key = "formula_rows" if cell_mode == "formula" else "value_rows"
        _write_rebuilt_sheet(
            rebuilt,
            rows=extracted_sheet.get(rows_key, []),
            note_lines=note_lines,
            cell_mode=cell_mode,
        )
        return RecoveryUnit(
            unit_type="sheet",
            unit_name=sheet_name,
            status="merged",
            fidelity="structure_rebuilt",
            message=message,
            recovery_steps=recovery_steps,
        )
    except Exception as exc:  # noqa: BLE001
        if rebuilt is not None:
            _delete_sheet(rebuilt)
        failure_message = f"{message} Rebuild also failed: {exc}"
        if original_error is not None:
            failure_message = f"{failure_message} (copy error: {original_error})"
        return RecoveryUnit(
            unit_type="sheet",
            unit_name=sheet_name,
            status="skipped",
            fidelity="skipped",
            message=failure_message,
            recovery_steps=(*recovery_steps, "rebuild_failed"),
        )


def _source_recovery_from_units(
    units: list[RecoveryUnit],
    base_steps: tuple[str, ...] = (),
    *,
    fallback_message: str | None = None,
) -> RecoveryInfo:
    merged_units = [unit for unit in units if unit.status == "merged"]
    skipped_units = [unit for unit in units if unit.status == "skipped"]
    if not merged_units:
        return RecoveryInfo(
            status="skipped",
            fidelity="skipped",
            message=fallback_message or "All sheets were skipped during rescue.",
            recovery_steps=dedupe_steps((*base_steps, "source_skipped")),
            units=tuple(units),
        )

    fidelity = worst_fidelity(unit.fidelity for unit in merged_units)
    messages: list[str] = []
    if fidelity == "structure_rebuilt":
        messages.append("One or more sheets were rebuilt from extracted cells.")
    elif fidelity == "retry_recovered":
        messages.append("One or more sheets succeeded after retry.")
    if skipped_units:
        messages.append(f"{len(skipped_units)} sheet(s) were skipped after rescue attempts.")
    if fallback_message:
        messages.append(fallback_message)
    return RecoveryInfo(
        status="merged",
        fidelity=fidelity,
        message=" ".join(dict.fromkeys(message for message in messages if message)) or None,
        recovery_steps=dedupe_steps((*base_steps, *(step for unit in units for step in unit.recovery_steps))),
        units=tuple(units),
    )


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
            return [[cell for cell in _row_values(row)] for row in value]
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


def _freeze_sheet_values(sheet: object) -> None:
    used = sheet.UsedRange
    used.Value = used.Value


def _reset_to_single_sheet(workbook: object) -> None:
    while workbook.Worksheets.Count > 1:
        workbook.Worksheets(workbook.Worksheets.Count).Delete()


def _source_lines(source: dict[str, Any], recovery: RecoveryInfo | None = None) -> list[str]:
    lines = [
        "Source workbook",
        f"Relative path: {source['relative_path']}",
        f"Absolute path: {source['absolute_path']}",
        f"Modified: {source.get('modified_at') or ''}",
        f"Sheets: {source.get('sheet_count') or 0}",
    ]
    if recovery is not None:
        lines.extend(["", *source_recovery_lines(recovery)])
    return lines


def _write_lines(sheet: object, lines: list[str]) -> None:
    for row, line in enumerate(lines, start=1):
        sheet.Cells(row, 1).Value = line
    used = sheet.UsedRange
    used.Columns.AutoFit()
    sheet.Rows(1).Font.Bold = True


def _write_rebuilt_sheet(
    sheet: object,
    *,
    rows: list[list[str]],
    note_lines: list[str],
    cell_mode: str,
) -> None:
    _write_lines(sheet, note_lines)
    start_row = len(note_lines) + 2
    for row_index, row in enumerate(rows, start=start_row):
        for column_index, value in enumerate(row, start=1):
            cell = sheet.Cells(row_index, column_index)
            if cell_mode == "formula" and isinstance(value, str) and value.startswith("="):
                cell.Formula = value
            else:
                cell.Value = value
    used = sheet.UsedRange
    used.Columns.AutoFit()


def _delete_sheet(sheet: object) -> None:
    try:
        sheet.Delete()
    except Exception:  # noqa: BLE001
        return


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
