from __future__ import annotations

from pathlib import Path

from file_merge_tool.application import merge_word as merge_word_module
from file_merge_tool.application.merge_word import merge_word
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
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
            return ExtractedWord(page_count=3, leading_text="\u6a5f\u5bc6 minutes")
        return ExtractedWord(page_count=2, leading_text="open minutes")

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
    assert [path.name for path in result.output_paths] == [
        "merged.docx",
        "merged_\u6a5f\u5bc6.docx",
    ]
    assert written[0][2][0]["relative_path"] == "normal.docx"
    assert written[1][2][0]["relative_path"] == "leading-marker.docm"
    assert "Classification: sensitive" in written[1][1]
