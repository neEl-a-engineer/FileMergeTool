from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from file_merge_tool.application.merge_pdf import merge_pdf
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest


def test_pdf_merge_writes_normal_and_sensitive_pdfs(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write_pdf(root / "normal.pdf", "normal document")
    _write_pdf(root / "secret_\u6a5f\u5bc6.pdf", "\u6a5f\u5bc6 document")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.pdf",
        output_stem="merged",
        exclude=ExcludeConfig(),
        kind="pdf-merge",
    )

    result = merge_pdf(request)

    assert result.item_count == 2
    assert len(result.output_paths) == 4
    normal_reader = PdfReader(str(result.output_paths[0]))
    sensitive_reader = PdfReader(str(result.output_paths[1]))
    assert len(normal_reader.pages) == 3
    assert len(sensitive_reader.pages) == 3
    assert result.output_paths[0].name == "merged_\u30de\u30fc\u30b8.pdf"
    assert result.output_paths[1].name == "\u6a5f\u5bc6_merged_\u30de\u30fc\u30b8.pdf"
    assert result.output_paths[2].name == "merged_\u30de\u30fc\u30b8.json"
    assert result.output_paths[3].name == "\u6a5f\u5bc6_merged_\u30de\u30fc\u30b8.json"


def _write_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.drawString(72, 720, text)
    pdf.save()
