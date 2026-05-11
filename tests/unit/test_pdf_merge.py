from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from file_merge_tool.application import merge_pdf as merge_pdf_module
from file_merge_tool.application.merge_pdf import merge_pdf
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.recovery import MergeWriteReport, RecoveryInfo, RecoveryUnit


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


def test_pdf_merge_records_page_level_recovery(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write_pdf(root / "normal.pdf", "normal document")

    def fake_write(path: Path, *, header_lines, sources):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"pdf")
        if not sources:
            return MergeWriteReport(output_path=path, recoveries=())
        recovery = RecoveryInfo(
            status="merged",
            fidelity="text_only",
            message="Page 1 was rebuilt as a text-only page.",
            recovery_steps=("page_add_failed", "rebuild_text_only"),
            units=(
                RecoveryUnit(
                    unit_type="page",
                    unit_name="Page 1",
                    status="merged",
                    fidelity="text_only",
                    message="Page 1 rebuilt.",
                    recovery_steps=("page_add_failed", "rebuild_text_only"),
                ),
            ),
        )
        return MergeWriteReport(output_path=path, recoveries=((sources[0]["absolute_path"], recovery),))

    monkeypatch.setattr(merge_pdf_module, "write_pdf_merge", fake_write)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.pdf",
        output_stem="merged",
        exclude=ExcludeConfig(),
        kind="pdf-merge",
    )

    result = merge_pdf(request)

    assert result.item_count == 1
    assert any("normal.pdf: merge_rescued" == warning for warning in result.warnings)
    payload = json.loads((tmp_path / "out" / "merged_マージ.json").read_text(encoding="utf-8"))
    assert payload["items"][0]["items"][0]["merge_recovery"]["fidelity"] == "text_only"


def _write_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.drawString(72, 720, text)
    pdf.save()
