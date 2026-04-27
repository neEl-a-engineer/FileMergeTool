from __future__ import annotations

from pathlib import Path
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
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.domain.sensitivity import SENSITIVE_MARKERS
from file_merge_tool.extractors.image_extractor import extract_image_file, is_image_file
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.image_html_writer import write_image_html_report
from file_merge_tool.writers.image_powerpoint_writer import write_image_powerpoint


def merge_image(request: MergeRequest) -> MergeResult:
    formats = request.image_output_formats or ("pptx",)
    unsupported = [fmt for fmt in formats if fmt not in {"html", "pptx"}]
    if unsupported:
        raise NotImplementedError(
            f"Unsupported image output format: {', '.join(unsupported)}"
        )

    scanned_items = list(walk_tree(request.root_path, request.exclude))
    normal_items: list[dict[str, Any]] = []
    sensitive_items: list[dict[str, Any]] = []
    skipped_items: list[SkippedItem] = []
    warnings: list[WarningItem] = []
    skipped_count = 0
    error_skipped_count = 0

    markers = _sensitivity_markers(request)

    for item in scanned_items:
        if item.kind != "file":
            if item.excluded:
                skipped_count += 1
                skipped_items.append(_skipped_item(item.relative_path, item.kind, item.excluded_reason or "skipped", item.absolute_path, item.link_target))
            continue

        if item.excluded:
            skipped_count += 1
            skipped_items.append(_skipped_item(item.relative_path, item.kind, item.excluded_reason or "excluded", item.absolute_path, item.link_target))
            continue

        if not is_image_file(item.absolute_path):
            skipped_count += 1
            skipped_items.append(_skipped_item(item.relative_path, item.kind, "not_image_extension", item.absolute_path, None))
            continue

        try:
            extracted = extract_image_file(item.absolute_path)
        except Exception as exc:  # noqa: BLE001
            skipped_count += 1
            error_skipped_count += 1
            skipped_items.append(_skipped_item(item.relative_path, item.kind, "read_error", item.absolute_path, None))
            warnings.append(
                WarningItem(
                    relative_path=item.relative_path,
                    reason="read_error",
                    message="Skipped because the image file could not be read.",
                    exception_type=exc.__class__.__name__,
                )
            )
            continue

        matched_markers = _matched_markers(str(item.absolute_path), markers)
        image_item = {
            "id": f"item-{len(normal_items) + len(sensitive_items) + 1:04d}",
            "absolute_path": str(item.absolute_path),
            "relative_path": item.relative_path,
            "modified_at": item.modified_at,
            "mime_type": extracted.mime_type,
            "width": extracted.width,
            "height": extracted.height,
            "file_size_bytes": extracted.file_size_bytes,
            "data_uri": extracted.data_uri,
            "sensitivity": {
                "classified": bool(matched_markers),
                "matched_markers": matched_markers,
            },
        }
        if matched_markers:
            sensitive_items.append(image_item)
        else:
            normal_items.append(image_item)

    output_stem = _output_stem(request)
    output_paths: list[Path] = []
    if "html" in formats:
        output_paths.append(
            _write_html(
                request=request,
                output_path=merge_output_path(
                    request,
                    extension=".html",
                    default_name=output_stem,
                ),
                classification="normal",
                items=normal_items,
                skipped_items=skipped_items,
                warnings=warnings,
                skipped_count=skipped_count,
                error_skipped_count=error_skipped_count,
            )
        )
        output_paths.append(
            _write_html(
                request=request,
                output_path=merge_output_path(
                    request,
                    extension=".html",
                    default_name=output_stem,
                    classification="sensitive",
                ),
                classification="sensitive",
                items=sensitive_items,
                skipped_items=skipped_items,
                warnings=warnings,
                skipped_count=skipped_count,
                error_skipped_count=error_skipped_count,
            )
        )

    if "pptx" in formats:
        output_paths.append(
            _write_pptx(
                request=request,
                output_path=merge_output_path(
                    request,
                    extension=".pptx",
                    default_name=output_stem,
                ),
                classification="normal",
                items=normal_items,
                skipped_items=skipped_items,
                warnings=warnings,
                skipped_count=skipped_count,
                error_skipped_count=error_skipped_count,
            )
        )
        output_paths.append(
            _write_pptx(
                request=request,
                output_path=merge_output_path(
                    request,
                    extension=".pptx",
                    default_name=output_stem,
                    classification="sensitive",
                ),
                classification="sensitive",
                items=sensitive_items,
                skipped_items=skipped_items,
                warnings=warnings,
                skipped_count=skipped_count,
                error_skipped_count=error_skipped_count,
            )
        )

    return MergeResult(
        output_paths=tuple(output_paths),
        item_count=len(normal_items) + len(sensitive_items),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(f"{item.relative_path}: {item.reason}" for item in warnings),
    )


def _write_html(
    *,
    request: MergeRequest,
    output_path: Path,
    classification: str,
    items: list[dict[str, Any]],
    skipped_items: list[SkippedItem],
    warnings: list[WarningItem],
    skipped_count: int,
    error_skipped_count: int,
) -> Path:
    summary = ArtifactSummary(
        item_count=len(items),
        skipped_count=skipped_count,
        error_skipped_count=error_skipped_count,
        warning_count=len(warnings),
    ).dict()
    header = build_artifact_header(
        request,
        schema_name="file-merge-tool/image-html-report/v1",
        kind=request.kind or "image-merge",
        classification=classification,
    )
    return write_image_html_report(
        output_path,
        title=f"Image Merge Report ({classification})",
        header=header,
        summary=summary,
        items=items,
        skipped_items=[model_to_dict(item, exclude_none=True) for item in skipped_items],
        warnings=[model_to_dict(item, exclude_none=True) for item in warnings],
    )


def _write_pptx(
    *,
    request: MergeRequest,
    output_path: Path,
    classification: str,
    items: list[dict[str, Any]],
    skipped_items: list[SkippedItem],
    warnings: list[WarningItem],
    skipped_count: int,
    error_skipped_count: int,
) -> Path:
    summary = ArtifactSummary(
        item_count=len(items),
        skipped_count=skipped_count,
        error_skipped_count=error_skipped_count,
        warning_count=len(warnings),
    ).dict()
    header = build_artifact_header(
        request,
        schema_name="file-merge-tool/image-pptx-merge/v1",
        kind=request.kind or "image-merge",
        classification=classification,
    )
    return write_image_powerpoint(
        output_path,
        title=f"Image Merge ({classification})",
        header=header,
        summary=summary,
        items=items,
        skipped_items=[model_to_dict(item, exclude_none=True) for item in skipped_items],
        warnings=[model_to_dict(item, exclude_none=True) for item in warnings],
    )


def _output_stem(request: MergeRequest) -> str:
    if request.output_folder_name:
        return request.output_folder_name
    if request.output_stem:
        return request.output_stem
    return Path(request.output_name).stem or "images"


def _sensitivity_markers(request: MergeRequest) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*SENSITIVE_MARKERS, *request.sensitivity_markers)))


def _matched_markers(value: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker and marker in value]


def _skipped_item(
    relative_path: str,
    kind: str,
    reason: str,
    absolute_path: Path,
    link_target: str | None,
) -> SkippedItem:
    return SkippedItem(
        relative_path=relative_path,
        kind=kind,
        reason=reason,
        absolute_path=str(absolute_path),
        link_target=link_target,
    )
