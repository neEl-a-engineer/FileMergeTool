from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedPdf:
    reader: PdfReader
    page_count: int
    first_page_text: str


def is_pdf_file(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def extract_pdf_file(path: Path) -> ExtractedPdf:
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    first_page_text = ""
    if page_count:
        first_page_text = reader.pages[0].extract_text() or ""
    return ExtractedPdf(reader=reader, page_count=page_count, first_page_text=first_page_text)
