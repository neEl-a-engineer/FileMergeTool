from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.domain.sensitivity import SENSITIVE_MARKERS
from file_merge_tool.extractors.powerpoint_extractor import (
    extract_powerpoint_file,
    is_powerpoint_file,
)
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.powerpoint_writer import write_powerpoint_merge


SENSITIVE_SUFFIX = "_\u6a5f\u5bc6"


def merge_powerpoint(request: MergeRequest) -> MergeResult:
    scanned_items = list(walk_tree(request.root_path, request.exclude))
    normal_sources: list[dict[str, Any]] = []
    sensitive_sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    skipped_count = 0
    error_skipped_count = 0
    markers = _sensitivity_markers(request)

    for item in scanned_items:
        if item.kind != "file":
            if item.excluded:
                skipped_count += 1
            continue
        if item.excluded:
            skipped_count += 1
            continue
        if not is_powerpoint_file(item.absolute_path):
            skipped_count += 1
            continue

        try:
            extracted = extract_powerpoint_file(item.absolute_path)
        except Exception as exc:  # noqa: BLE001
            skipped_count += 1
            error_skipped_count += 1
            warnings.append(f"{item.relative_path}: read_error:{exc.__class__.__name__}")
            continue

        matched_markers = _matched_markers(
            f"{item.absolute_path.name}\n{extracted.first_slide_text}",
            markers,
        )
        source = {
            "absolute_path": str(item.absolute_path),
            "relative_path": item.relative_path,
            "modified_at": item.modified_at,
            "slide_count": extracted.slide_count,
            "matched_markers": matched_markers,
        }
        if matched_markers:
            sensitive_sources.append(source)
        else:
            normal_sources.append(source)

    output_stem = _output_stem(request)
    normal_path = request.output_dir / f"{output_stem}.pptx"
    sensitive_path = request.output_dir / f"{output_stem}{SENSITIVE_SUFFIX}.pptx"

    write_powerpoint_merge(
        normal_path,
        header_lines=_header_lines(request, "normal", normal_sources, skipped_count, warnings),
        sources=normal_sources,
    )
    write_powerpoint_merge(
        sensitive_path,
        header_lines=_header_lines(request, "sensitive", sensitive_sources, skipped_count, warnings),
        sources=sensitive_sources,
    )

    return MergeResult(
        output_paths=(normal_path, sensitive_path),
        item_count=len(normal_sources) + len(sensitive_sources),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(warnings),
    )


def _header_lines(
    request: MergeRequest,
    classification: str,
    sources: list[dict[str, Any]],
    skipped_count: int,
    warnings: list[str],
) -> list[str]:
    return [
        "Tool: file-merge-tool",
        "Schema: file-merge-tool/powerpoint-merge/v1",
        f"Job ID: {request.job_id or ''}",
        f"Kind: {request.kind or 'powerpoint-merge'}",
        f"Classification: {classification}",
        f"Source root: {request.root_path.resolve()}",
        f"Setting name: {request.setting_name or ''}",
        "Traversal: files-first-depth-first-name-asc",
        "Follow symlinks: false",
        f"Exclude folders: {', '.join(request.exclude.folder_names)}",
        f"Exclude extensions: {', '.join(request.exclude.extensions)}",
        f"Exclude file names: {', '.join(request.exclude.file_names)}",
        f"Sensitivity markers: {', '.join(_sensitivity_markers(request))}",
        f"Source presentations: {len(sources)}",
        f"Skipped items: {skipped_count}",
        f"Warnings: {len(warnings)}",
    ]


def _output_stem(request: MergeRequest) -> str:
    if request.output_stem:
        return request.output_stem
    return Path(request.output_name).stem or "powerpoint-merge"


def _sensitivity_markers(request: MergeRequest) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*SENSITIVE_MARKERS, *request.sensitivity_markers)))


def _matched_markers(value: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker and marker in value]
