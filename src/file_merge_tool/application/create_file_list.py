from __future__ import annotations

from typing import Any

from file_merge_tool.domain.artifact import (
    ArtifactSummary,
    SkippedItem,
    build_artifact_header,
    model_to_dict,
)
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.json_writer import write_json


def create_file_list(request: MergeRequest) -> MergeResult:
    items = list(walk_tree(request.root_path, request.exclude))
    skipped_items = [
        SkippedItem(
            relative_path=item.relative_path,
            kind=item.kind,
            reason=item.excluded_reason or "excluded",
            absolute_path=str(item.absolute_path),
            link_target=item.link_target,
        )
        for item in items
        if item.excluded
    ]
    excluded_count = sum(1 for item in items if item.excluded)
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
        "items": [
            {
                "absolute_path": str(item.absolute_path),
                "relative_path": item.relative_path,
                "kind": item.kind,
                "modified_at": item.modified_at,
                "excluded": item.excluded,
                "excluded_reason": item.excluded_reason,
                "link_target": item.link_target,
            }
            for item in items
        ],
        "skipped_items": [model_to_dict(item, exclude_none=True) for item in skipped_items],
        "warnings": [],
    }

    output_path = request.output_dir / request.output_name
    write_json(output_path, payload)
    return MergeResult(
        output_paths=(output_path,),
        item_count=len(items),
        skipped_count=excluded_count,
        excluded_count=excluded_count,
    )


def default_output_name() -> str:
    return "file-list.json"
