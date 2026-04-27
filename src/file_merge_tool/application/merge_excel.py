from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.application.output_files import merge_output_path
from file_merge_tool.domain.artifact import (
    ArtifactSummary,
    SkippedItem,
    WarningItem,
    build_artifact_header,
    model_to_dict,
)
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.domain.sensitivity import SENSITIVE_MARKERS
from file_merge_tool.extractors.excel_extractor import extract_excel_file, is_excel_file
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.excel_writer import write_excel_merge
from file_merge_tool.writers.json_writer import write_json


FORMULA_LABEL = "数式"
VALUE_LABEL = "値"


def merge_excel(request: MergeRequest) -> MergeResult:
    scanned_items = list(walk_tree(request.root_path, request.exclude))
    normal_sources: list[dict[str, Any]] = []
    sensitive_sources: list[dict[str, Any]] = []
    skipped_items: list[SkippedItem] = []
    warnings: list[WarningItem] = []
    skipped_count = 0
    error_skipped_count = 0
    markers = _sensitivity_markers(request)

    for item in scanned_items:
        if item.kind != "file":
            if item.excluded:
                skipped_count += 1
                skipped_items.append(_skipped_item(item, item.excluded_reason or "skipped"))
            continue
        if item.excluded:
            skipped_count += 1
            skipped_items.append(_skipped_item(item, item.excluded_reason or "excluded"))
            continue
        if not is_excel_file(item.absolute_path):
            skipped_count += 1
            skipped_items.append(_skipped_item(item, "not_excel_extension"))
            continue

        try:
            extracted = extract_excel_file(item.absolute_path)
        except Exception as exc:  # noqa: BLE001
            skipped_count += 1
            error_skipped_count += 1
            skipped_items.append(_skipped_item(item, "read_error"))
            warnings.append(
                WarningItem(
                    relative_path=item.relative_path,
                    reason="read_error",
                    message="Skipped because the Excel file could not be read.",
                    exception_type=exc.__class__.__name__,
                )
            )
            continue

        matched_markers = _matched_markers(
            f"{item.absolute_path.name}\n{extracted.first_sheet_text}",
            markers,
        )
        source = {
            "absolute_path": str(item.absolute_path),
            "relative_path": item.relative_path,
            "modified_at": item.modified_at,
            "sheet_count": extracted.sheet_count,
            "sheets": extracted.sheets,
            "sensitivity": {
                "classified": bool(matched_markers),
                "matched_markers": matched_markers,
            },
        }
        if matched_markers:
            sensitive_sources.append(source)
        else:
            normal_sources.append(source)

    output_base = _output_base(request)
    outputs: list[Path] = []
    for label, mode in ((FORMULA_LABEL, "formula"), (VALUE_LABEL, "value")):
        normal_xlsx = merge_output_path(
            request,
            extension=".xlsx",
            default_name=output_base,
            parts=[label],
        )
        sensitive_xlsx = merge_output_path(
            request,
            extension=".xlsx",
            default_name=output_base,
            classification="sensitive",
            parts=[label],
        )
        normal_json = merge_output_path(
            request,
            extension=".json",
            default_name=output_base,
            parts=[label],
        )
        sensitive_json = merge_output_path(
            request,
            extension=".json",
            default_name=output_base,
            classification="sensitive",
            parts=[label],
        )

        write_excel_merge(
            normal_xlsx,
            header_lines=_header_lines(request, "normal", normal_sources, skipped_count, warnings, mode),
            sources=normal_sources,
            cell_mode=mode,
        )
        write_excel_merge(
            sensitive_xlsx,
            header_lines=_header_lines(request, "sensitive", sensitive_sources, skipped_count, warnings, mode),
            sources=sensitive_sources,
            cell_mode=mode,
        )
        _write_merge_json(
            request=request,
            output_path=normal_json,
            classification="normal",
            items=normal_sources,
            scanned_items=scanned_items,
            skipped_items=skipped_items,
            warnings=warnings,
            skipped_count=skipped_count,
            error_skipped_count=error_skipped_count,
            cell_mode=mode,
        )
        _write_merge_json(
            request=request,
            output_path=sensitive_json,
            classification="sensitive",
            items=sensitive_sources,
            scanned_items=scanned_items,
            skipped_items=skipped_items,
            warnings=warnings,
            skipped_count=skipped_count,
            error_skipped_count=error_skipped_count,
            cell_mode=mode,
        )
        outputs.extend((normal_xlsx, sensitive_xlsx, normal_json, sensitive_json))

    return MergeResult(
        output_paths=tuple(outputs),
        item_count=len(normal_sources) + len(sensitive_sources),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(f"{item.relative_path}: {item.reason}" for item in warnings),
    )


def _write_merge_json(
    *,
    request: MergeRequest,
    output_path: Path,
    classification: str,
    items: list[dict[str, Any]],
    scanned_items: list[Any],
    skipped_items: list[SkippedItem],
    warnings: list[WarningItem],
    skipped_count: int,
    error_skipped_count: int,
    cell_mode: str,
) -> Path:
    payload = {
        "schema": "file-merge-tool/excel-merge-json/v1",
        "header": build_artifact_header(
            request,
            schema_name="file-merge-tool/excel-merge-json/v1",
            kind=request.kind or "excel-merge",
            classification=classification,
        ),
        "cell_mode": cell_mode,
        "summary": ArtifactSummary(
            item_count=len(items),
            skipped_count=skipped_count,
            excluded_count=sum(1 for item in scanned_items if item.excluded),
            error_skipped_count=error_skipped_count,
            warning_count=len(warnings),
        ).dict(),
        "items": [_json_item(item, cell_mode=cell_mode) for item in items],
        "skipped_items": [model_to_dict(item, exclude_none=True) for item in skipped_items],
        "warnings": [model_to_dict(item, exclude_none=True) for item in warnings],
    }
    write_json(output_path, payload)
    return output_path


def _json_item(item: dict[str, Any], *, cell_mode: str) -> dict[str, Any]:
    row_key = "formula_rows" if cell_mode == "formula" else "value_rows"
    return {
        "absolute_path": item["absolute_path"],
        "relative_path": item["relative_path"],
        "modified_at": item["modified_at"],
        "sheet_count": item["sheet_count"],
        "sensitivity": item["sensitivity"],
        "sheets": [
            {
                "sheet_name": sheet["sheet_name"],
                "sheet_order": sheet["sheet_order"],
                "used_range": sheet["used_range"],
                "rows": sheet[row_key],
            }
            for sheet in item["sheets"]
        ],
    }


def _header_lines(
    request: MergeRequest,
    classification: str,
    sources: list[dict[str, Any]],
    skipped_count: int,
    warnings: list[WarningItem],
    cell_mode: str,
) -> list[str]:
    return [
        "Tool: file-merge-tool",
        "Schema: file-merge-tool/excel-merge/v2",
        f"Job ID: {request.job_id or ''}",
        f"Kind: {request.kind or 'excel-merge'}",
        f"Classification: {classification}",
        f"Cell mode: {cell_mode}",
        f"Source root: {request.root_path.resolve()}",
        f"Setting name: {request.setting_name or ''}",
        "Traversal: files-first-depth-first-name-asc",
        "Follow symlinks: false",
        f"Exclude folders: {', '.join(request.exclude.folder_names)}",
        f"Exclude extensions: {', '.join(request.exclude.extensions)}",
        f"Exclude file names: {', '.join(request.exclude.file_names)}",
        f"Sensitivity markers: {', '.join(_sensitivity_markers(request))}",
        f"Source workbooks: {len(sources)}",
        f"Skipped items: {skipped_count}",
        f"Warnings: {len(warnings)}",
    ]


def _output_base(request: MergeRequest) -> str:
    if request.output_folder_name:
        return request.output_folder_name
    if request.output_stem:
        return request.output_stem
    return Path(request.output_name).stem or "excel-merge"


def _sensitivity_markers(request: MergeRequest) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*SENSITIVE_MARKERS, *request.sensitivity_markers)))


def _matched_markers(value: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker and marker in value]


def _skipped_item(item: Any, reason: str) -> SkippedItem:
    return SkippedItem(
        relative_path=item.relative_path,
        kind=item.kind,
        reason=reason,
        absolute_path=str(item.absolute_path),
        link_target=item.link_target,
    )
