from __future__ import annotations

from pathlib import Path

from file_merge_tool.domain.config import ExcludeConfig
from file_merge_tool.domain.file_item import ScannedItem
from file_merge_tool.domain.source_target import SourceTargetScan
from file_merge_tool.scanning.exclude_rules import ExcludeRules
from file_merge_tool.scanning.timestamps import modified_at_iso
from file_merge_tool.scanning.walker import walk_tree


def scan_source_targets(
    source_targets: tuple[Path, ...],
    exclude: ExcludeConfig,
) -> tuple[SourceTargetScan, ...]:
    rules = ExcludeRules.from_config(exclude)
    covered_paths: list[Path] = []
    scans: list[SourceTargetScan] = []

    for requested in source_targets:
        requested_path = requested.absolute()
        if not requested_path.exists():
            scans.append(
                SourceTargetScan(
                    requested_path=requested_path,
                    source_target_path=requested_path,
                    kind="missing",
                    status="skipped",
                    reason="path_not_found",
                )
            )
            continue

        if requested_path.is_symlink():
            scans.append(
                SourceTargetScan(
                    requested_path=requested_path,
                    source_target_path=requested_path,
                    kind="symlink",
                    status="skipped",
                    reason="symlink_not_followed",
                    items=(
                        ScannedItem(
                            absolute_path=requested_path.absolute(),
                            relative_path=".",
                            relative_path_from_target=".",
                            source_target_path=str(requested_path.absolute()),
                            source_target_kind="symlink",
                            kind="symlink",
                            modified_at=modified_at_iso(requested_path),
                            excluded=True,
                            excluded_reason="symlink_not_followed",
                            link_target=_link_target(requested_path),
                        ),
                    ),
                    link_target=_link_target(requested_path),
                )
            )
            continue

        resolved = _safe_resolve(requested_path)
        target_kind = _target_kind(requested_path)
        if _is_fully_covered(resolved, covered_paths):
            scans.append(
                SourceTargetScan(
                    requested_path=requested_path,
                    source_target_path=resolved,
                    kind=target_kind,
                    status="skipped",
                    reason="covered_by_previous_target",
                )
            )
            continue

        if requested_path.is_file():
            reason = rules.file_reason(requested_path)
            item = ScannedItem(
                absolute_path=resolved,
                relative_path=".",
                relative_path_from_target=".",
                source_target_path=str(resolved),
                source_target_kind="file",
                kind="file",
                modified_at=modified_at_iso(requested_path),
                excluded=reason is not None,
                excluded_reason=reason,
            )
            scans.append(
                SourceTargetScan(
                    requested_path=requested_path,
                    source_target_path=resolved,
                    kind="file",
                    status="scanned",
                    items=(item,),
                )
            )
            covered_paths.append(resolved)
            continue

        if requested_path.is_dir():
            reason = rules.folder_reason(requested_path)
            if reason is not None:
                root_item = ScannedItem(
                    absolute_path=resolved,
                    relative_path=".",
                    relative_path_from_target=".",
                    source_target_path=str(resolved),
                    source_target_kind="folder",
                    kind="folder",
                    modified_at=modified_at_iso(requested_path),
                    excluded=True,
                    excluded_reason=reason,
                )
                scans.append(
                    SourceTargetScan(
                        requested_path=requested_path,
                        source_target_path=resolved,
                        kind="folder",
                        status="scanned",
                        items=(root_item,),
                    )
                )
                covered_paths.append(resolved)
                continue

            items = tuple(
                walk_tree(
                    requested_path,
                    exclude,
                    source_target_path=resolved,
                    source_target_kind="folder",
                    covered_paths=tuple(covered_paths),
                )
            )
            scans.append(
                SourceTargetScan(
                    requested_path=requested_path,
                    source_target_path=resolved,
                    kind="folder",
                    status="scanned",
                    items=items,
                )
            )
            covered_paths.append(resolved)
            continue

        scans.append(
            SourceTargetScan(
                requested_path=requested_path,
                source_target_path=resolved,
                kind="other",
                status="skipped",
                reason="unsupported_file_type",
                items=(
                    ScannedItem(
                        absolute_path=resolved,
                        relative_path=".",
                        relative_path_from_target=".",
                        source_target_path=str(resolved),
                        source_target_kind="other",
                        kind="other",
                        modified_at=modified_at_iso(requested_path),
                        excluded=True,
                        excluded_reason="unsupported_file_type",
                    ),
                ),
            )
        )

    return tuple(scans)


def flatten_scanned_items(target_scans: tuple[SourceTargetScan, ...]) -> list[ScannedItem]:
    return [item for scan in target_scans for item in scan.items]


def _is_fully_covered(path: Path, covered_paths: list[Path]) -> bool:
    for covered in covered_paths:
        if path == covered:
            return True
        if covered.is_dir():
            try:
                path.relative_to(covered)
            except ValueError:
                continue
            return True
    return False


def _target_kind(path: Path) -> str:
    if path.is_file():
        return "file"
    if path.is_dir():
        return "folder"
    return "other"


def _safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _link_target(path: Path) -> str | None:
    try:
        return str(path.readlink())
    except OSError:
        return None
