from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractedText:
    encoding: str
    lines: list[str]


def extract_text(path: Path) -> ExtractedText:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        return ExtractedText(encoding=encoding, lines=text.splitlines())
    text = data.decode("utf-8", errors="replace")
    return ExtractedText(encoding="utf-8-replace", lines=text.splitlines())

