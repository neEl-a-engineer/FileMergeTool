from __future__ import annotations

from pathlib import Path

from file_merge_tool.application import merge_powerpoint as merge_powerpoint_module
from file_merge_tool.application.merge_powerpoint import merge_powerpoint
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.extractors.powerpoint_extractor import ExtractedPowerPoint


def test_powerpoint_merge_splits_normal_and_sensitive_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "normal.pptx").write_bytes(b"placeholder")
    (root / "first-slide-marker.pptx").write_bytes(b"placeholder")

    def fake_extract(path: Path) -> ExtractedPowerPoint:
        if path.name == "first-slide-marker.pptx":
            return ExtractedPowerPoint(slide_count=3, first_slide_text="\u6a5f\u5bc6 agenda")
        return ExtractedPowerPoint(slide_count=2, first_slide_text="open agenda")

    written: list[tuple[Path, list[str], list[dict[str, object]]]] = []

    def fake_write(path: Path, *, header_lines, sources):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"pptx")
        written.append((path, header_lines, sources))
        return path

    monkeypatch.setattr(merge_powerpoint_module, "extract_powerpoint_file", fake_extract)
    monkeypatch.setattr(merge_powerpoint_module, "write_powerpoint_merge", fake_write)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.pptx",
        output_stem="merged",
        exclude=ExcludeConfig(),
        kind="powerpoint-merge",
    )

    result = merge_powerpoint(request)

    assert result.item_count == 2
    assert [path.name for path in result.output_paths] == [
        "merged.pptx",
        "merged_\u6a5f\u5bc6.pptx",
    ]
    assert len(written[0][2]) == 1
    assert written[0][2][0]["relative_path"] == "normal.pptx"
    assert len(written[1][2]) == 1
    assert written[1][2][0]["relative_path"] == "first-slide-marker.pptx"
    assert "Classification: sensitive" in written[1][1]
