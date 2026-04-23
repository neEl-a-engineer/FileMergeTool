from __future__ import annotations

from pathlib import Path


DEFAULT_TEXT_EXTENSIONS = frozenset(
    {
        ".bat",
        ".cmd",
        ".conf",
        ".css",
        ".csv",
        ".env",
        ".html",
        ".ini",
        ".js",
        ".json",
        ".jsx",
        ".log",
        ".md",
        ".ps1",
        ".py",
        ".rst",
        ".sh",
        ".sql",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)


def has_text_extension(path: Path) -> bool:
    return path.suffix.lower() in DEFAULT_TEXT_EXTENSIONS

