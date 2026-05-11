from __future__ import annotations

import json
from pathlib import Path

from file_merge_tool.application import merge_powerpoint as merge_powerpoint_module
from file_merge_tool.application.merge_powerpoint import merge_powerpoint
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.recovery import MergeWriteReport, RecoveryInfo, RecoveryUnit
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
            return ExtractedPowerPoint(
                slide_count=3,
                first_slide_text="\u6a5f\u5bc6 agenda",
                slides=[{"slide_number": 1, "text_lines": ["\u6a5f\u5bc6 agenda"]}],
            )
        return ExtractedPowerPoint(
            slide_count=2,
            first_slide_text="open agenda",
            slides=[{"slide_number": 1, "text_lines": ["open agenda"]}],
        )

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
    assert [path.name for path in result.output_paths[:2]] == [
        "merged_\u30de\u30fc\u30b8.pptx",
        "\u6a5f\u5bc6_merged_\u30de\u30fc\u30b8.pptx",
    ]
    assert [path.name for path in result.output_paths[2:]] == [
        "merged_\u30de\u30fc\u30b8.json",
        "\u6a5f\u5bc6_merged_\u30de\u30fc\u30b8.json",
    ]
    assert len(written[0][2]) == 1
    assert written[0][2][0]["relative_path"] == "normal.pptx"
    assert len(written[1][2]) == 1
    assert written[1][2][0]["relative_path"] == "first-slide-marker.pptx"
    assert "Classification: sensitive" in written[1][1]


def test_powerpoint_merge_records_text_only_recovery(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "deck.pptx").write_bytes(b"placeholder")

    def fake_extract(path: Path) -> ExtractedPowerPoint:
        return ExtractedPowerPoint(
            slide_count=1,
            first_slide_text="open agenda",
            slides=[{"slide_number": 1, "text_lines": ["open agenda"]}],
        )

    def fake_write(path: Path, *, header_lines, sources):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"pptx")
        if not sources:
            return MergeWriteReport(output_path=path, recoveries=())
        recovery = RecoveryInfo(
            status="merged",
            fidelity="text_only",
            message="Slide 1 was rebuilt as a text-only slide.",
            recovery_steps=("slide_insert_failed", "rebuild_text_only"),
            units=(
                RecoveryUnit(
                    unit_type="slide",
                    unit_name="Slide 1",
                    status="merged",
                    fidelity="text_only",
                    message="Slide 1 rebuilt.",
                    recovery_steps=("slide_insert_failed", "rebuild_text_only"),
                ),
            ),
        )
        return MergeWriteReport(output_path=path, recoveries=((sources[0]["absolute_path"], recovery),))

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

    assert result.item_count == 1
    assert any("deck.pptx: merge_rescued" == warning for warning in result.warnings)
    payload = json.loads((tmp_path / "out" / "merged_マージ.json").read_text(encoding="utf-8"))
    assert payload["items"][0]["items"][0]["merge_recovery"]["fidelity"] == "text_only"
