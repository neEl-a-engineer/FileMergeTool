from __future__ import annotations

from typing import Any

from file_merge_tool.domain.artifact import SkippedItem, WarningItem
from file_merge_tool.domain.recovery import MergeWriteReport, RecoveryInfo, recovery_to_dict
from file_merge_tool.domain.result import FileResult


def apply_write_report(
    *,
    sources: list[dict[str, Any]],
    report: MergeWriteReport,
    warnings: list[WarningItem],
    skipped_items: list[SkippedItem],
    file_results: list[FileResult],
) -> tuple[list[dict[str, Any]], int, int]:
    kept_sources: list[dict[str, Any]] = []
    skipped_count = 0
    error_skipped_count = 0
    recovery_map = report.recovery_map()

    for source in sources:
        absolute_path = str(source["absolute_path"])
        recovery = recovery_map.get(absolute_path) or RecoveryInfo()
        source["merge_recovery"] = recovery_to_dict(recovery)
        if recovery.status == "skipped":
            skipped_count += 1
            error_skipped_count += 1
            skipped_items.append(
                SkippedItem(
                    relative_path=source["relative_path"],
                    kind="file",
                    reason="merge_error",
                    source_target_path=source.get("source_target_path"),
                    source_target_kind=source.get("source_target_kind"),
                    absolute_path=absolute_path,
                )
            )
            warnings.append(
                WarningItem(
                    relative_path=source["relative_path"],
                    reason="merge_error",
                    message=recovery.message or "The file could not be merged into the output artifact.",
                    source_target_path=source.get("source_target_path"),
                    source_target_kind=source.get("source_target_kind"),
                )
            )
            _replace_file_result(
                file_results,
                absolute_path=absolute_path,
                update={
                    "status": "error",
                    "skip_reason": "merge_error",
                    "message": "The file could not be merged into the output artifact.",
                    "details": recovery.message,
                    "recovery": recovery_to_dict(recovery),
                },
            )
            continue

        if recovery.fidelity != "exact":
            warnings.append(
                WarningItem(
                    relative_path=source["relative_path"],
                    reason="merge_rescued",
                    message=recovery.message or "The file was merged with rescue fallback steps.",
                    source_target_path=source.get("source_target_path"),
                    source_target_kind=source.get("source_target_kind"),
                )
            )
        _replace_file_result(
            file_results,
            absolute_path=absolute_path,
            update={
                "recovery": recovery_to_dict(recovery),
                "details": recovery.message,
            },
        )
        kept_sources.append(source)

    return kept_sources, skipped_count, error_skipped_count


def _replace_file_result(
    file_results: list[FileResult],
    *,
    absolute_path: str,
    update: dict[str, Any],
) -> None:
    for index, item in enumerate(file_results):
        if item.source_path != absolute_path:
            continue
        payload = item.__dict__.copy()
        payload.update({key: value for key, value in update.items() if value is not None})
        file_results[index] = FileResult(**payload)
        return

