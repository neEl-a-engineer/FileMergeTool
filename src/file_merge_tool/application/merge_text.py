from __future__ import annotations

from typing import Any

from file_merge_tool.domain.artifact import (
    ArtifactSummary,
    SkippedItem,
    WarningItem,
    build_artifact_header,
    model_to_dict,
)
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.extractors.text_extractor import extract_text
from file_merge_tool.scanning.file_type import has_text_extension
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.json_writer import write_json


def merge_text(request: MergeRequest) -> MergeResult:
    scanned_items = list(walk_tree(request.root_path, request.exclude))
    files: list[dict[str, Any]] = []
    warnings: list[WarningItem] = []
    skipped_items: list[SkippedItem] = []
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
            continue
        if not has_text_extension(item.absolute_path):
            skipped_count += 1
            skipped_items.append(
                SkippedItem(
                    relative_path=item.relative_path,
                    kind=item.kind,
                    reason="not_text_extension",
                    absolute_path=str(item.absolute_path),
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

    output_path = request.output_dir / request.output_name
    write_json(output_path, payload)
    return MergeResult(
        output_paths=(output_path,),
        item_count=len(files),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(f"{item.relative_path}: {item.reason}" for item in warnings),
    )


def default_output_name() -> str:
    return "text-merge.json"
