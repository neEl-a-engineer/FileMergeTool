from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.domain.output_naming import SUMMARY_LABEL, classification_for_name


EXTERNAL_PREVIEW_EXTENSIONS = {
    ".doc",
    ".docm",
    ".docx",
    ".pdf",
    ".ppt",
    ".pptm",
    ".pptx",
    ".xls",
    ".xlsb",
    ".xlsm",
    ".xlsx",
}


def build_output_record(path: Path) -> dict[str, Any]:
    category = "summary" if path.suffix.lower() == ".json" and path.stem.endswith(f"_{SUMMARY_LABEL}") else "merge"
    variant = None
    if "_数式_" in path.stem:
        variant = "formula"
    elif "_値_" in path.stem:
        variant = "value"
    preview_mode = _preview_mode(path)
    return {
        "classification": classification_for_name(path.name),
        "category": category,
        "format": path.suffix.lstrip(".").lower(),
        "variant": variant,
        "path": str(path),
        "download_name": path.name,
        "preview_mode": preview_mode,
    }


def _preview_mode(path: Path) -> str | None:
    extension = path.suffix.lower()
    if extension == ".json":
        return "json"
    if extension in EXTERNAL_PREVIEW_EXTENSIONS:
        return "external"
    return None
