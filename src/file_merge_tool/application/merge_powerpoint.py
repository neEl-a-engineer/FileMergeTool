from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.application.merge_recovery import apply_write_report
from file_merge_tool.application.output_files import merge_output_path
from file_merge_tool.application.source_target_reporting import (
    build_target_level_file_results,
    build_target_level_skipped_items,
)
from file_merge_tool.application.target_groups import build_target_item_groups
from file_merge_tool.domain.artifact import (
    ArtifactSummary,
    SkippedItem,
    WarningItem,
    build_artifact_header,
    model_to_dict,
)
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.extension_selection import effective_selected_extensions, is_extension_selected
from file_merge_tool.domain.recovery import coerce_write_report
from file_merge_tool.domain.result import FileResult, MergeResult
from file_merge_tool.domain.rule_matching import matched_literal_substrings, matched_regex_patterns
from file_merge_tool.domain.sensitivity import SENSITIVE_MARKERS
from file_merge_tool.extractors.powerpoint_extractor import (
    extract_powerpoint_file,
    is_powerpoint_file,
)
from file_merge_tool.scanning.source_targets import flatten_scanned_items, scan_source_targets
from file_merge_tool.writers.json_writer import write_json
from file_merge_tool.writers.powerpoint_writer import write_powerpoint_merge


def merge_powerpoint(request: MergeRequest) -> MergeResult:
    target_scans = scan_source_targets(request.source_targets or (request.root_path,), request.exclude)
    scanned_items = flatten_scanned_items(target_scans)
    normal_sources: list[dict[str, Any]] = []
    sensitive_sources: list[dict[str, Any]] = []
    skipped_items: list[SkippedItem] = build_target_level_skipped_items(target_scans)
    warnings: list[WarningItem] = []
    file_results: list[FileResult] = build_target_level_file_results(target_scans)
    skipped_count = len(skipped_items)
    error_skipped_count = 0
    markers = _sensitivity_markers(request)

    for item in scanned_items:
        if item.kind != "file":
            if item.excluded:
                skipped_count += 1
                skipped_items.append(_skipped_item(item, item.excluded_reason or "skipped"))
                file_results.append(
                    FileResult(
                        relative_path=item.relative_path,
                        source_path=str(item.absolute_path),
                        source_target_path=item.source_target_path,
                        source_target_kind=item.source_target_kind,
                        status="skipped",
                        skip_reason=item.excluded_reason or "skipped",
                        details="The path matched an exclusion rule during traversal.",
                    )
                )
            continue
        if item.excluded:
            skipped_count += 1
            skipped_items.append(_skipped_item(item, item.excluded_reason or "excluded"))
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
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
            kind=request.kind or "powerpoint-merge",
        ):
            skipped_count += 1
            skipped_items.append(_skipped_item(item, "extension_not_selected"))
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
                    status="skipped",
                    skip_reason="extension_not_selected",
                    details="The file extension is not selected for this merge run.",
                )
            )
            continue
        if not is_powerpoint_file(item.absolute_path):
            skipped_count += 1
            skipped_items.append(_skipped_item(item, "reader_not_available"))
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
                    status="skipped",
                    skip_reason="reader_not_available",
                    details="The file extension is selected, but no PowerPoint reader is available for it.",
                )
            )
            continue

        try:
            extracted = extract_powerpoint_file(item.absolute_path)
        except Exception as exc:  # noqa: BLE001
            skipped_count += 1
            error_skipped_count += 1
            skipped_items.append(_skipped_item(item, "read_error"))
            warnings.append(
                WarningItem(
                    relative_path=item.relative_path,
                    reason="read_error",
                    message="Skipped because the PowerPoint file could not be read.",
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
                    exception_type=exc.__class__.__name__,
                )
            )
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
                    status="error",
                    skip_reason="read_error",
                    exception_type=exc.__class__.__name__,
                    message="The PowerPoint file could not be read.",
                    details=str(exc),
                )
            )
            continue

        matched_markers = _matched_markers(
            [item.absolute_path.name, extracted.first_slide_text],
            markers,
            request.sensitivity_patterns,
        )
        source = {
            "absolute_path": str(item.absolute_path),
            "relative_path": item.relative_path,
            "relative_path_from_target": item.relative_path_from_target,
            "source_target_path": item.source_target_path,
            "source_target_kind": item.source_target_kind,
            "modified_at": item.modified_at,
            "slide_count": extracted.slide_count,
            "slides": extracted.slides,
            "sensitivity": {
                "classified": bool(matched_markers),
                "matched_markers": matched_markers,
            },
        }
        if matched_markers:
            sensitive_sources.append(source)
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
                    status="merged",
                    classification="confidential",
                )
            )
        else:
            normal_sources.append(source)
            file_results.append(
                FileResult(
                    relative_path=item.relative_path,
                    source_path=str(item.absolute_path),
                    source_target_path=item.source_target_path,
                    source_target_kind=item.source_target_kind,
                    status="merged",
                    classification="normal",
                )
            )

    output_base = _output_base(request)
    normal_pptx = merge_output_path(request, extension=".pptx", default_name=output_base)
    sensitive_pptx = merge_output_path(
        request,
        extension=".pptx",
        default_name=output_base,
        classification="sensitive",
    )
    normal_json = merge_output_path(request, extension=".json", default_name=output_base)
    sensitive_json = merge_output_path(
        request,
        extension=".json",
        default_name=output_base,
        classification="sensitive",
    )

    normal_report = coerce_write_report(
        write_powerpoint_merge(
            normal_pptx,
            header_lines=_header_lines(request, "normal", normal_sources, skipped_count, warnings),
            sources=normal_sources,
        ),
        normal_sources,
    )
    sensitive_report = coerce_write_report(
        write_powerpoint_merge(
            sensitive_pptx,
            header_lines=_header_lines(request, "sensitive", sensitive_sources, skipped_count, warnings),
            sources=sensitive_sources,
        ),
        sensitive_sources,
    )
    normal_sources, normal_skipped, normal_error_skipped = apply_write_report(
        sources=normal_sources,
        report=normal_report,
        warnings=warnings,
        skipped_items=skipped_items,
        file_results=file_results,
    )
    sensitive_sources, sensitive_skipped, sensitive_error_skipped = apply_write_report(
        sources=sensitive_sources,
        report=sensitive_report,
        warnings=warnings,
        skipped_items=skipped_items,
        file_results=file_results,
    )
    skipped_count += normal_skipped + sensitive_skipped
    error_skipped_count += normal_error_skipped + sensitive_error_skipped
    _write_merge_json(
        request=request,
        output_path=normal_json,
        classification="normal",
        items=normal_sources,
        target_scans=target_scans,
        scanned_items=scanned_items,
        skipped_items=skipped_items,
        warnings=warnings,
        skipped_count=skipped_count,
        error_skipped_count=error_skipped_count,
    )
    _write_merge_json(
        request=request,
        output_path=sensitive_json,
        classification="sensitive",
        items=sensitive_sources,
        target_scans=target_scans,
        scanned_items=scanned_items,
        skipped_items=skipped_items,
        warnings=warnings,
        skipped_count=skipped_count,
        error_skipped_count=error_skipped_count,
    )

    return MergeResult(
        output_paths=(normal_report.output_path, sensitive_report.output_path, normal_json, sensitive_json),
        item_count=len(normal_sources) + len(sensitive_sources),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(f"{item.relative_path}: {item.reason}" for item in warnings),
        file_results=tuple(file_results),
    )


def _write_merge_json(
    *,
    request: MergeRequest,
    output_path: Path,
    classification: str,
    items: list[dict[str, Any]],
    target_scans: tuple[Any, ...],
    scanned_items: list[Any],
    skipped_items: list[SkippedItem],
    warnings: list[WarningItem],
    skipped_count: int,
    error_skipped_count: int,
) -> Path:
    payload = {
        "schema": "file-merge-tool/powerpoint-merge-json/v1",
        "header": build_artifact_header(
            request,
            schema_name="file-merge-tool/powerpoint-merge-json/v1",
            kind=request.kind or "powerpoint-merge",
            classification=classification,
        ),
        "summary": ArtifactSummary(
            item_count=len(items),
            skipped_count=skipped_count,
            excluded_count=sum(1 for item in scanned_items if item.excluded),
            error_skipped_count=error_skipped_count,
            warning_count=len(warnings),
            rescued_count=sum(1 for item in items if (item.get("merge_recovery") or {}).get("fidelity") not in (None, "exact")),
            rescued_unit_count=sum(
                1
                for item in items
                for unit in (item.get("merge_recovery") or {}).get("units", [])
                if unit.get("status") == "merged" and unit.get("fidelity") != "exact"
            ),
            skipped_unit_count=sum(
                1
                for item in items
                for unit in (item.get("merge_recovery") or {}).get("units", [])
                if unit.get("status") == "skipped"
            ),
        ).dict(),
        "items": build_target_item_groups(
            target_scans,
            merged_items=items,
            skipped_items=skipped_items,
            warnings=warnings,
        ),
        "skipped_items": [model_to_dict(item, exclude_none=True) for item in skipped_items],
        "warnings": [model_to_dict(item, exclude_none=True) for item in warnings],
    }
    write_json(output_path, payload)
    return output_path


def _header_lines(
    request: MergeRequest,
    classification: str,
    sources: list[dict[str, Any]],
    skipped_count: int,
    warnings: list[WarningItem],
) -> list[str]:
    return [
        "Tool: file-merge-tool",
        "Schema: file-merge-tool/powerpoint-merge/v2",
        f"Job ID: {request.job_id or ''}",
        f"Kind: {request.kind or 'powerpoint-merge'}",
        f"Classification: {classification}",
        f"Source root: {request.root_path.resolve()}",
        f"Setting name: {request.setting_name or ''}",
        "Traversal: files-first-depth-first-name-asc",
        "Follow symlinks: false",
        f"Selected extensions: {', '.join(request.selected_extensions)}",
        f"Additional extensions: {', '.join(request.additional_extensions)}",
        "Effective extensions: "
        + ", ".join(
            effective_selected_extensions(
                request.selected_extensions,
                request.additional_extensions,
                kind=request.kind,
            )
        ),
        f"Exclude folders: {', '.join(request.exclude.folder_names)}",
        f"Exclude folder regex: {', '.join(request.exclude.folder_patterns)}",
        f"Exclude file names: {', '.join(request.exclude.file_names)}",
        f"Exclude file regex: {', '.join(request.exclude.file_patterns)}",
        f"Sensitivity markers: {', '.join(_sensitivity_markers(request))}",
        f"Sensitivity regex: {', '.join(request.sensitivity_patterns)}",
        f"Source presentations: {len(sources)}",
        f"Skipped items: {skipped_count}",
        f"Warnings: {len(warnings)}",
    ]


def _output_base(request: MergeRequest) -> str:
    if request.output_folder_name:
        return request.output_folder_name
    if request.output_stem:
        return request.output_stem
    return Path(request.output_name).stem or "powerpoint-merge"


def _sensitivity_markers(request: MergeRequest) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*SENSITIVE_MARKERS, *request.sensitivity_markers)))


def _matched_markers(
    haystacks: list[str],
    markers: tuple[str, ...],
    regex_patterns: tuple[str, ...],
) -> list[str]:
    return [
        *matched_literal_substrings(haystacks, markers),
        *matched_regex_patterns(haystacks, regex_patterns),
    ]


def _skipped_item(item: Any, reason: str) -> SkippedItem:
    return SkippedItem(
        relative_path=item.relative_path,
        kind=item.kind,
        reason=reason,
        source_target_path=item.source_target_path,
        source_target_kind=item.source_target_kind,
        absolute_path=str(item.absolute_path),
        link_target=item.link_target,
    )
