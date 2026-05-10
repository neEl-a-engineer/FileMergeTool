from __future__ import annotations

from typing import Any

from file_merge_tool.domain.artifact import SkippedItem, WarningItem, model_to_dict
from file_merge_tool.domain.source_target import SourceTargetScan


def build_target_item_groups(
    target_scans: tuple[SourceTargetScan, ...],
    *,
    merged_items: list[dict[str, Any]],
    skipped_items: list[SkippedItem],
    warnings: list[WarningItem],
) -> list[dict[str, Any]]:
    merged_by_target = _group_dicts_by_target(merged_items)
    skipped_by_target = _group_models_by_target(skipped_items)
    warnings_by_target = _group_models_by_target(warnings)

    groups: list[dict[str, Any]] = []
    for target in target_scans:
        key = target.key
        target_merged = merged_by_target.get(key, [])
        target_skipped = skipped_by_target.get(key, [])
        target_warnings = warnings_by_target.get(key, [])
        groups.append(
            {
                "source_target_path": str(target.source_target_path),
                "requested_target_path": str(target.requested_path),
                "source_target_kind": target.kind,
                "status": _status_for_target(target, target_merged, target_skipped, target_warnings),
                "reason": target.reason,
                "summary": {
                    "item_count": len(target_merged),
                    "skipped_count": len(target_skipped),
                    "warning_count": len(target_warnings),
                },
                "items": target_merged,
                "skipped_items": target_skipped,
                "warnings": target_warnings,
            }
        )
    return groups


def _group_dicts_by_target(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        key = str(item.get("source_target_path", ""))
        grouped.setdefault(key, []).append(item)
    return grouped


def _group_models_by_target(items: list[Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        payload = model_to_dict(item, exclude_none=True)
        key = str(payload.get("source_target_path", ""))
        grouped.setdefault(key, []).append(payload)
    return grouped


def _status_for_target(
    target: SourceTargetScan,
    merged_items: list[dict[str, Any]],
    skipped_items: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    if target.reason and not merged_items and not skipped_items and not warnings:
        return "skipped"
    if merged_items and (skipped_items or warnings or target.reason):
        return "completed_with_skips"
    if merged_items:
        return "completed"
    if skipped_items or warnings or target.reason:
        return "skipped"
    return target.status
