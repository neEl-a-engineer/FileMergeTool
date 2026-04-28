from __future__ import annotations

from typing import Any

from file_merge_tool.domain.artifact import (
    ArtifactSummary,
    SkippedItem,
    WarningItem,
    build_artifact_header,
    model_to_dict,
)
from file_merge_tool.application.output_files import merge_output_path
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.extension_selection import is_extension_selected
from file_merge_tool.domain.result import FileResult, MergeResult
from file_merge_tool.extractors.text_extractor import extract_text
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.json_writer import write_json


def merge_text(request: MergeRequest) -> MergeResult:
    scanned_items = list(walk_tree(request.root_path, request.exclude))
    files: list[dict[str, Any]] = []
    warnings: list[WarningItem] = []
    skipped_items: list[SkippedItem] = []
    file_results: list[FileResult] = []
    skipped_count = 0
    error_skipped_count = 0

    for item in scanned_items:
        if item.kind != "file":
            if item.excluded:
                skipped_count += 1
                skipped_items.append(
                    SkippedItem(
                        relative_path=item.relative_path,
                        kind=item.kind,
                        reason=item.excluded_reason or "skipped",
                        absolute_path=str(item.absolute_path),
                        link_target=item.link_target,
                    )
                )
                file_results.append(
                    FileResult(
                        relative_path=item.relative_path,
                        source_path=str(item.absolute_path),
                        status="skipped",
                        skip_reason=item.excluded_reason or "skipped",
                        details="The path matched an exclusion rule during traversal.",
                    )
                )
            continue
        if item.excluded:
            skipped_count += 1
            skipped_items.append(
                SkippedItem(
                    relative_path=item.relative_path,
                    kind=item.kind,
                    reason=item.excluded_reason or "excluded",
                    absolute_path=str(item.absolute_path),
                )
            )
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    status="skipped",
                    skip_reason=item.excluded_reason or "excluded",
                    details="The file matched an exclusion rule.",
                )
            )
            continue
        if not is_extension_selected(
            item.absolute_path,
            selected_extensions=request.selected_extensions,
            additional_extensions=request.additional_extensions,
            kind=request.kind or "text-merge",
        ):
            skipped_count += 1
            skipped_items.append(
                SkippedItem(
                    relative_path=item.relative_path,
                    kind=item.kind,
                    reason="extension_not_selected",
                    absolute_path=str(item.absolute_path),
                )
            )
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    status="skipped",
                    skip_reason="extension_not_selected",
                    details="The file extension is not selected for this merge run.",
                )
            )
            continue

        try:
            extracted = extract_text(item.absolute_path)
        except OSError as exc:
            skipped_count += 1
            error_skipped_count += 1
            skipped_items.append(
                SkippedItem(
                    relative_path=item.relative_path,
                    kind=item.kind,
                    reason="read_error",
                    absolute_path=str(item.absolute_path),
                    link_target=None,
                )
            )
            warnings.append(
                WarningItem(
                    relative_path=item.relative_path,
                    reason="read_error",
                    message="Skipped because the file could not be read.",
                    exception_type=exc.__class__.__name__,
                )
            )
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    status="error",
                    skip_reason="read_error",
                    exception_type=exc.__class__.__name__,
                    message="The text file could not be read.",
                    details=str(exc),
                )
            )
            continue

        files.append(
            {
                "absolute_path": str(item.absolute_path),
                "relative_path": item.relative_path,
                "modified_at": item.modified_at,
                "encoding": extracted.encoding,
                "line_count": len(extracted.lines),
                "sensitivity": {
                    "classified": False,
                    "matched_markers": [],
                },
                "lines": extracted.lines,
            }
        )
        file_results.append(
            FileResult(
                relative_path=item.relative_path,
                source_path=str(item.absolute_path),
                status="merged",
                classification="normal",
            )
        )

    payload: dict[str, Any] = {
        "schema": "file-merge-tool/text-merge/v1",
        "header": build_artifact_header(
            request,
            schema_name="file-merge-tool/text-merge/v1",
            kind=request.kind or "text-merge",
        ),
        "summary": ArtifactSummary(
            item_count=len(files),
            skipped_count=skipped_count,
            excluded_count=sum(1 for item in scanned_items if item.excluded),
            error_skipped_count=error_skipped_count,
            warning_count=len(warnings),
        ).dict(),
        "items": files,
        "skipped_items": [model_to_dict(item, exclude_none=True) for item in skipped_items],
        "warnings": [model_to_dict(item, exclude_none=True) for item in warnings],
    }

    output_path = merge_output_path(
        request,
        extension=".json",
        default_name="text-merge",
    )
    write_json(output_path, payload)
    return MergeResult(
        output_paths=(output_path,),
        item_count=len(files),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(f"{item.relative_path}: {item.reason}" for item in warnings),
        file_results=tuple(file_results),
    )


def default_output_name() -> str:
    return "text-merge.json"
