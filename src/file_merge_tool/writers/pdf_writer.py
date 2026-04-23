from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


def write_pdf_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_page(_text_page("Merge Header", header_lines))

    for source in sources:
        writer.add_page(_text_page("Source", _source_lines(source)))
        reader = source["reader"]
        for page in reader.pages:
            writer.add_page(page)

    with path.open("wb") as file:
        writer.write(file)
    return path


def _source_lines(source: dict[str, Any]) -> list[str]:
    return [
        f"Relative path: {source['relative_path']}",
        f"Absolute path: {source['absolute_path']}",
        f"Modified: {source.get('modified_at') or ''}",
        f"Pages: {source.get('page_count') or 0}",
    ]


def _text_page(title: str, lines: list[str]):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_name = _font_name()
    pdf.setFont(font_name, 18)
    pdf.drawString(42, height - 54, title)
    pdf.setFont(font_name, 9)
    y = height - 84
    for line in lines:
        for wrapped in _wrap_line(line, 110):
            if y < 42:
                pdf.showPage()
                pdf.setFont(font_name, 9)
                y = height - 54
            pdf.drawString(42, y, wrapped)
            y -= 14
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def _font_name() -> str:
    font_name = "HeiseiKakuGo-W5"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        return font_name
    except Exception:  # noqa: BLE001
        return "Helvetica"


def _wrap_line(line: str, size: int) -> list[str]:
    if len(line) <= size:
        return [line]
    return [line[index : index + size] for index in range(0, len(line), size)]
