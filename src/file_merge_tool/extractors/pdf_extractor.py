from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedPdf:
    reader: PdfReader
    page_count: int
    first_page_text: str
    pages: list[dict[str, object]]


def is_pdf_file(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def extract_pdf_file(path: Path) -> ExtractedPdf:
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    first_page_text = ""
    pages: list[dict[str, object]] = []
    if page_count:
        for page_index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            lines = text.splitlines()
            if page_index == 1:
                first_page_text = text
            pages.append(
                {
                    "page_number": page_index,
                    "text_lines": lines,
                }
            )
    return ExtractedPdf(
        reader=reader,
        page_count=page_count,
        first_page_text=first_page_text,
        pages=pages,
    )
