from __future__ import annotations

from pathlib import Path

from file_merge_tool.domain.config import normalize_extension_values
from file_merge_tool.domain.merge_job import MergeKind


TEXT_EXTENSION_OPTIONS = (
    ".bat",
    ".c",
    ".cmd",
    ".conf",
    ".cpp",
    ".css",
    ".cs",
    ".csv",
    ".env",
    ".gitignore",
    ".go",
    ".h",
    ".html",
    ".hpp",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".log",
    ".md",
    ".php",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".rst",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
)

KIND_EXTENSION_OPTIONS: dict[str, tuple[str, ...]] = {
    MergeKind.TEXT_MERGE.value: TEXT_EXTENSION_OPTIONS,
    MergeKind.MAIL_MERGE.value: (".msg",),
    MergeKind.POWERPOINT_MERGE.value: (
        ".ppt",
        ".pptm",
        ".pps",
        ".ppsm",
        ".ppsx",
        ".pot",
        ".potm",
        ".potx",
        ".pptx",
    ),
    MergeKind.EXCEL_MERGE.value: (
        ".csv",
        ".ods",
        ".tsv",
        ".xls",
        ".xlsb",
        ".xlsm",
        ".xlsx",
        ".xlt",
        ".xltm",
        ".xltx",
    ),
    MergeKind.WORD_MERGE.value: (
        ".doc",
        ".docm",
        ".docx",
        ".dot",
        ".dotm",
        ".dotx",
        ".odt",
        ".rtf",
    ),
    MergeKind.PDF_MERGE.value: (".pdf",),
    MergeKind.IMAGE_MERGE.value: (
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    ),
}


def extension_options_for_kind(kind: str | None) -> tuple[str, ...]:
    return KIND_EXTENSION_OPTIONS.get(kind or "", ())


def default_selected_extensions(kind: str | None) -> tuple[str, ...]:
    return extension_options_for_kind(kind)


def effective_selected_extensions(
    selected_extensions: tuple[str, ...] | list[str],
    additional_extensions: tuple[str, ...] | list[str],
    *,
    kind: str | None = None,
) -> tuple[str, ...]:
    selected = normalize_extension_values(selected_extensions or default_selected_extensions(kind))
    additional = normalize_extension_values(additional_extensions)
    return tuple(dict.fromkeys((*selected, *additional)))


def path_extension_token(path: Path) -> str:
    if path.suffix:
        return path.suffix
    if path.name.startswith(".") and path.name.count(".") == 1:
        return path.name
    return ""


def is_extension_selected(
    path: Path,
    *,
    selected_extensions: tuple[str, ...] | list[str],
    additional_extensions: tuple[str, ...] | list[str],
    kind: str | None = None,
) -> bool:
    extension_name = path_extension_token(path)
    if not extension_name:
        return False
    return extension_name in effective_selected_extensions(
        selected_extensions,
        additional_extensions,
        kind=kind,
    )
