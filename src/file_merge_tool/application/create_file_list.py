from __future__ import annotations

from typing import Any

from file_merge_tool.domain.artifact import (
    ArtifactSummary,
    SkippedItem,
    build_artifact_header,
    model_to_dict,
)
from file_merge_tool.application.source_target_reporting import (
    build_target_level_file_results,
    build_target_level_skipped_items,
)
from file_merge_tool.application.target_groups import build_target_item_groups
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import FileResult, MergeResult
from file_merge_tool.application.output_files import file_list_output_path
from file_merge_tool.scanning.source_targets import flatten_scanned_items, scan_source_targets
from file_merge_tool.writers.json_writer import write_json


def create_file_list(request: MergeRequest) -> MergeResult:
    target_scans = scan_source_targets(request.source_targets or (request.root_path,), request.exclude)
    items = flatten_scanned_items(target_scans)
    file_results = [
        FileResult(
            relative_path=item.relative_path,
            source_path=str(item.absolute_path),
            source_target_path=item.source_target_path,
            source_target_kind=item.source_target_kind,
            status="skipped" if item.excluded else "merged",
            skip_reason=item.excluded_reason if item.excluded else None,
            details="The path matched an exclusion rule during traversal." if item.excluded else None,
        )
        for item in items
    ]
    skipped_items = [
        SkippedItem(
            relative_path=item.relative_path,
            kind=item.kind,
            reason=item.excluded_reason or "excluded",
            source_target_path=item.source_target_path,
            source_target_kind=item.source_target_kind,
            absolute_path=str(item.absolute_path),
            link_target=item.link_target,
        )
        for item in items
        if item.excluded
    ]
    skipped_items.extend(build_target_level_skipped_items(target_scans))
    file_results.extend(build_target_level_file_results(target_scans))
    excluded_count = sum(1 for item in items if item.excluded)
    grouped_items = build_target_item_groups(
        target_scans,
        merged_items=[
            {
                "absolute_path": str(item.absolute_path),
                "relative_path": item.relative_path,
                "relative_path_from_target": item.relative_path_from_target,
                "source_target_path": item.source_target_path,
                "source_target_kind": item.source_target_kind,
                "kind": item.kind,
                "modified_at": item.modified_at,
                "excluded": item.excluded,
                "excluded_reason": item.excluded_reason,
                "link_target": item.link_target,
            }
            for item in items
        ],
        skipped_items=skipped_items,
        warnings=[],
    )
    payload: dict[str, Any] = {
        "schema": "file-merge-tool/file-list/v1",
        "header": build_artifact_header(
            request,
            schema_name="file-merge-tool/file-list/v1",
            kind=request.kind or "file-list",
        ),
        "summary": ArtifactSummary(
            item_count=len(items),
            excluded_count=excluded_count,
            skipped_count=excluded_count,
        ).dict(),
        "items": grouped_items,
        "skipped_items": [model_to_dict(item, exclude_none=True) for item in skipped_items],
        "warnings": [],
    }

    output_path = file_list_output_path(request, default_name="file-list")
    write_json(output_path, payload)
    return MergeResult(
        output_paths=(output_path,),
        item_count=len(items),
        skipped_count=len(skipped_items),
        excluded_count=excluded_count,
        file_results=tuple(file_results),
    )


def default_output_name() -> str:
    return "file-list.json"
