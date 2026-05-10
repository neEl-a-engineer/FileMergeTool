from __future__ import annotations

from file_merge_tool.domain.artifact import SkippedItem
from file_merge_tool.domain.result import FileResult
from file_merge_tool.domain.source_target import SourceTargetScan


def build_target_level_skipped_items(
    target_scans: tuple[SourceTargetScan, ...],
) -> list[SkippedItem]:
    items: list[SkippedItem] = []
    for target in target_scans:
        if not target.reason or target.items:
            continue
        items.append(
            SkippedItem(
                relative_path=".",
                kind=target.kind,
                reason=target.reason,
                source_target_path=str(target.source_target_path),
                source_target_kind=target.kind,
                absolute_path=str(target.source_target_path),
                link_target=target.link_target,
            )
        )
    return items


def build_target_level_file_results(
    target_scans: tuple[SourceTargetScan, ...],
) -> list[FileResult]:
    results: list[FileResult] = []
    for target in target_scans:
        if not target.reason or target.items:
            continue
        results.append(
            FileResult(
                relative_path=".",
                source_path=str(target.source_target_path),
                source_target_path=str(target.source_target_path),
                source_target_kind=target.kind,
                status="skipped",
                skip_reason=target.reason,
                details="The source target could not be scanned.",
            )
        )
    return results
