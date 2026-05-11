from __future__ import annotations

import json
from pathlib import Path

from file_merge_tool.application import merge_word as merge_word_module
from file_merge_tool.application.merge_word import merge_word
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.recovery import MergeWriteReport, RecoveryInfo
from file_merge_tool.extractors.word_extractor import ExtractedWord


def test_word_merge_splits_normal_and_sensitive_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "normal.docx").write_bytes(b"placeholder")
    (root / "leading-marker.docm").write_bytes(b"placeholder")

    def fake_extract(path: Path) -> ExtractedWord:
        if path.name == "leading-marker.docm":
            return ExtractedWord(
                page_count=3,
                leading_text="\u6a5f\u5bc6 minutes",
                lines=["\u6a5f\u5bc6 minutes", "line 2"],
            )
        return ExtractedWord(page_count=2, leading_text="open minutes", lines=["open minutes"])

    written: list[tuple[Path, list[str], list[dict[str, object]]]] = []

    def fake_write(path: Path, *, header_lines, sources):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"docx")
        written.append((path, header_lines, sources))
        return path

    monkeypatch.setattr(merge_word_module, "extract_word_file", fake_extract)
    monkeypatch.setattr(merge_word_module, "write_word_merge", fake_write)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.docx",
        output_stem="merged",
        exclude=ExcludeConfig(),
        kind="word-merge",
    )

    result = merge_word(request)

    assert result.item_count == 2
    assert [path.name for path in result.output_paths[:2]] == [
        "merged_\u30de\u30fc\u30b8.docx",
        "\u6a5f\u5bc6_merged_\u30de\u30fc\u30b8.docx",
    ]
    assert [path.name for path in result.output_paths[2:]] == [
        "merged_\u30de\u30fc\u30b8.json",
        "\u6a5f\u5bc6_merged_\u30de\u30fc\u30b8.json",
    ]
    assert written[0][2][0]["relative_path"] == "normal.docx"
    assert written[1][2][0]["relative_path"] == "leading-marker.docm"
    assert "Classification: sensitive" in written[1][1]


def test_word_merge_skips_source_when_writer_reports_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "broken.docx").write_bytes(b"placeholder")

    def fake_extract(path: Path) -> ExtractedWord:
        return ExtractedWord(page_count=1, leading_text="open minutes", lines=["open minutes"])

    def fake_write(path: Path, *, header_lines, sources):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"docx")
        if not sources:
            return MergeWriteReport(output_path=path, recoveries=())
        recovery = RecoveryInfo(
            status="skipped",
            fidelity="skipped",
            message="The document could not be inserted or rebuilt.",
            recovery_steps=("document_insert_failed", "rebuild_text_only_failed"),
        )
        return MergeWriteReport(output_path=path, recoveries=((sources[0]["absolute_path"], recovery),))

    monkeypatch.setattr(merge_word_module, "extract_word_file", fake_extract)
    monkeypatch.setattr(merge_word_module, "write_word_merge", fake_write)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.docx",
        output_stem="merged",
        exclude=ExcludeConfig(),
        kind="word-merge",
    )

    result = merge_word(request)

    assert result.item_count == 0
    assert any("broken.docx: merge_error" == warning for warning in result.warnings)
    payload = json.loads((tmp_path / "out" / "merged_マージ.json").read_text(encoding="utf-8"))
    assert payload["items"][0]["summary"]["item_count"] == 0
