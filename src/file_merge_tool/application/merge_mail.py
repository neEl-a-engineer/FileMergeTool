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
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.domain.sensitivity import SENSITIVE_MARKERS
from file_merge_tool.extractors.msg_extractor import extract_msg_file, is_msg_file
from file_merge_tool.scanning.walker import walk_tree
from file_merge_tool.writers.json_writer import write_json


SENSITIVE_SUFFIX = "_\u6a5f\u5bc6"


def merge_mail(request: MergeRequest) -> MergeResult:
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
                skipped_items.append(
                    _skipped_item(
                        item.relative_path,
                        item.kind,
                        item.excluded_reason or "skipped",
                        item.absolute_path,
                        item.link_target,
                    )
                )
            continue

        if item.excluded:
            skipped_count += 1
            skipped_items.append(
                _skipped_item(
                    item.relative_path,
                    item.kind,
                    item.excluded_reason or "excluded",
                    item.absolute_path,
                    item.link_target,
                )
            )
            continue

        if not is_msg_file(item.absolute_path):
            skipped_count += 1
            skipped_items.append(
                _skipped_item(
                    item.relative_path,
                    item.kind,
                    "not_msg_extension",
                    item.absolute_path,
                    None,
                )
            )
            continue

        try:
            extracted = extract_msg_file(item.absolute_path)
        except Exception as exc:  # noqa: BLE001
            skipped_count += 1
            error_skipped_count += 1
            skipped_items.append(
                _skipped_item(
                    item.relative_path,
                    item.kind,
                    "read_error",
                    item.absolute_path,
                    None,
                )
            )
            warnings.append(
                WarningItem(
                    relative_path=item.relative_path,
                    reason="read_error",
                    message="Skipped because the .msg file could not be read.",
                    exception_type=exc.__class__.__name__,
                )
            )
            continue

        matched_markers = _matched_markers(
            extracted.subject,
            _first_non_empty_body_lines(extracted.body_lines, limit=3),
            markers,
        )
        mail_item = {
            "absolute_path": str(item.absolute_path),
            "relative_path": item.relative_path,
            "modified_at": item.modified_at,
            "subject": extracted.subject,
            "received_at": extracted.received_at,
            "sender": extracted.sender,
            "recipients": extracted.recipients,
            "body": {
                "line_count": len(extracted.body_lines),
                "lines": extracted.body_lines,
            },
            "attachment_names": extracted.attachment_names,
            "sensitivity": {
                "classified": bool(matched_markers),
                "matched_markers": matched_markers,
            },
        }
        if matched_markers:
            sensitive_items.append(mail_item)
        else:
            normal_items.append(mail_item)

    output_stem = _output_stem(request)
    output_paths = (
        _write_json(
            request=request,
            output_path=request.output_dir / f"{output_stem}.json",
            classification="normal",
            items=normal_items,
            scanned_items=scanned_items,
            skipped_items=skipped_items,
            warnings=warnings,
            skipped_count=skipped_count,
            error_skipped_count=error_skipped_count,
        ),
        _write_json(
            request=request,
            output_path=request.output_dir / f"{output_stem}{SENSITIVE_SUFFIX}.json",
            classification="sensitive",
            items=sensitive_items,
            scanned_items=scanned_items,
            skipped_items=skipped_items,
            warnings=warnings,
            skipped_count=skipped_count,
            error_skipped_count=error_skipped_count,
        ),
    )

    return MergeResult(
        output_paths=output_paths,
        item_count=len(normal_items) + len(sensitive_items),
        skipped_count=skipped_count,
        excluded_count=sum(1 for item in scanned_items if item.excluded),
        error_skipped_count=error_skipped_count,
        warnings=tuple(f"{item.relative_path}: {item.reason}" for item in warnings),
    )


def _write_json(
    *,
    request: MergeRequest,
    output_path: Path,
    classification: str,
    items: list[dict[str, Any]],
    scanned_items: list[Any],
    skipped_items: list[SkippedItem],
    warnings: list[WarningItem],
    skipped_count: int,
    error_skipped_count: int,
) -> Path:
    payload: dict[str, Any] = {
        "schema": "file-merge-tool/mail-merge/v1",
        "header": build_artifact_header(
            request,
            schema_name="file-merge-tool/mail-merge/v1",
            kind=request.kind or "mail-merge",
            classification=classification,
        ),
        "summary": ArtifactSummary(
            item_count=len(items),
            skipped_count=skipped_count,
            excluded_count=sum(1 for item in scanned_items if item.excluded),
            error_skipped_count=error_skipped_count,
            warning_count=len(warnings),
        ).dict(),
        "items": items,
        "skipped_items": [model_to_dict(item, exclude_none=True) for item in skipped_items],
        "warnings": [model_to_dict(item, exclude_none=True) for item in warnings],
    }
    write_json(output_path, payload)
    return output_path


def _output_stem(request: MergeRequest) -> str:
    if request.output_stem:
        return request.output_stem
    return Path(request.output_name).stem or "mail-merge"


def _sensitivity_markers(request: MergeRequest) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*SENSITIVE_MARKERS, *request.sensitivity_markers)))


def _first_non_empty_body_lines(lines: list[str], *, limit: int) -> list[str]:
    return [line for line in (value.strip() for value in lines) if line][:limit]


def _matched_markers(subject: str, body_lines: list[str], markers: tuple[str, ...]) -> list[str]:
    haystacks = [subject, *body_lines]
    return [
        marker
        for marker in markers
        if marker and any(marker in haystack for haystack in haystacks)
    ]


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
