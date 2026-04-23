from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MergeKind(str, Enum):
    FILE_LIST = "file-list"
    TEXT_MERGE = "text-merge"
    MAIL_MERGE = "mail-merge"
    POWERPOINT_MERGE = "powerpoint-merge"
    EXCEL_MERGE = "excel-merge"
    WORD_MERGE = "word-merge"
    PDF_MERGE = "pdf-merge"
    IMAGE_MERGE = "image-merge"


@dataclass(frozen=True)
class JobOutput:
    path: Path
    kind: MergeKind
