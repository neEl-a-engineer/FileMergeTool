from __future__ import annotations

from pathlib import Path
from typing import Iterable

from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.output_naming import (
    FILE_LIST_LABEL,
    SUMMARY_LABEL,
    compose_output_file_name,
    normalize_output_folder_name,
)


def output_folder_name(request: MergeRequest, *, default_name: str) -> str:
    return normalize_output_folder_name(
        request.output_folder_name,
        fallback_stem=request.output_stem,
        fallback_name=request.output_name,
        default_name=default_name,
    )


def merge_output_path(
    request: MergeRequest,
    *,
    extension: str,
    default_name: str,
    classification: str = "normal",
    parts: Iterable[str] = (),
) -> Path:
    folder_name = output_folder_name(request, default_name=default_name)
    return request.output_dir / compose_output_file_name(
        folder_name,
        extension=extension,
        classification=classification,
        parts=parts,
    )


def summary_output_path(request: MergeRequest, *, default_name: str) -> Path:
    folder_name = output_folder_name(request, default_name=default_name)
    return request.output_dir / compose_output_file_name(
        folder_name,
        extension=".json",
        suffix_label=SUMMARY_LABEL,
    )


def file_list_output_path(request: MergeRequest, *, default_name: str) -> Path:
    folder_name = output_folder_name(request, default_name=default_name)
    return request.output_dir / compose_output_file_name(
        folder_name,
        extension=".json",
        suffix_label=FILE_LIST_LABEL,
    )
