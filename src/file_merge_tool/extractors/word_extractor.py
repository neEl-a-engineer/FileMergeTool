from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from file_merge_tool.infrastructure.office_com.word import read_word_info


WORD_EXTENSIONS = frozenset(
    {
        ".doc",
        ".docm",
        ".docx",
        ".dot",
        ".dotm",
        ".dotx",
        ".odt",
        ".rtf",
    }
)


@dataclass(frozen=True)
class ExtractedWord:
    page_count: int
    leading_text: str
    lines: list[str]


def is_word_file(path: Path) -> bool:
    return path.suffix.lower() in WORD_EXTENSIONS


def extract_word_file(path: Path) -> ExtractedWord:
    info = read_word_info(path)
    return ExtractedWord(
        page_count=info["page_count"],
        leading_text=info["leading_text"],
        lines=info["lines"],
    )
