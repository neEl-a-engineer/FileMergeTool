from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from file_merge_tool.infrastructure.office_com.powerpoint import read_powerpoint_info


POWERPOINT_EXTENSIONS = frozenset(
    {
        ".ppt",
        ".pptx",
        ".pptm",
        ".pps",
        ".ppsx",
        ".ppsm",
        ".pot",
        ".potx",
        ".potm",
    }
)


@dataclass(frozen=True)
class ExtractedPowerPoint:
    slide_count: int
    first_slide_text: str


def is_powerpoint_file(path: Path) -> bool:
    return path.suffix.lower() in POWERPOINT_EXTENSIONS


def extract_powerpoint_file(path: Path) -> ExtractedPowerPoint:
    info = read_powerpoint_info(path)
    return ExtractedPowerPoint(
        slide_count=info["slide_count"],
        first_slide_text=info["first_slide_text"],
    )
