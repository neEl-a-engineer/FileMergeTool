from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


CONFIDENTIAL_PREFIX = "機密"
MERGE_LABEL = "マージ"
SUMMARY_LABEL = "集計"
FILE_LIST_LABEL = "構成リスト"

_INVALID_WINDOWS_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def normalize_output_folder_name(
    value: str | None,
    *,
    fallback_stem: str | None = None,
    fallback_name: str | None = None,
    default_name: str = "output",
) -> str:
    candidate = (value or "").strip()
    if not candidate and fallback_stem:
        candidate = fallback_stem.strip()
    if not candidate and fallback_name:
        candidate = Path(fallback_name).stem.strip()
    if not candidate:
        candidate = default_name
    candidate = _INVALID_WINDOWS_NAME.sub("_", candidate)
    candidate = candidate.rstrip(" .")
    return candidate or default_name


def compose_output_file_name(
    output_folder_name: str,
    *,
    extension: str,
    classification: str = "normal",
    parts: Iterable[str] = (),
    suffix_label: str = MERGE_LABEL,
) -> str:
    tokens: list[str] = []
    if classification == "sensitive":
        tokens.append(CONFIDENTIAL_PREFIX)
    tokens.append(output_folder_name)
    tokens.extend(part for part in parts if part)
    if suffix_label:
        tokens.append(suffix_label)
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"{'_'.join(tokens)}{ext}"


def classification_for_name(name: str) -> str:
    return "sensitive" if name.startswith(f"{CONFIDENTIAL_PREFIX}_") else "normal"
