from __future__ import annotations

from pathlib import Path

from file_merge_tool.application import merge_excel as merge_excel_module
from file_merge_tool.application.merge_excel import merge_excel
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.extractors.excel_extractor import ExtractedExcel


def test_excel_merge_splits_normal_and_sensitive_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "normal.xlsx").write_bytes(b"placeholder")
    (root / "first-sheet-marker.xlsm").write_bytes(b"placeholder")

    def fake_extract(path: Path) -> ExtractedExcel:
        if path.name == "first-sheet-marker.xlsm":
            return ExtractedExcel(
                sheet_count=3,
                first_sheet_text="\u6975\u79d8 budget",
                sheets=[
                    {
                        "sheet_name": "Sheet1",
                        "sheet_order": 1,
                        "formula_rows": [["=SUM(A1:A2)"]],
                        "value_rows": [["100"]],
                        "used_range": {"start_row": 1, "start_column": 1, "row_count": 1, "column_count": 1},
                    }
                ],
            )
        return ExtractedExcel(
            sheet_count=2,
            first_sheet_text="open budget",
            sheets=[
                {
                    "sheet_name": "Sheet1",
                    "sheet_order": 1,
                    "formula_rows": [["=A1"]],
                    "value_rows": [["open"]],
                    "used_range": {"start_row": 1, "start_column": 1, "row_count": 1, "column_count": 1},
                }
            ],
        )

    written: list[tuple[Path, list[str], list[dict[str, object]]]] = []

    def fake_write(path: Path, *, header_lines, sources, cell_mode="formula"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"xlsx")
        written.append((path, header_lines, sources, cell_mode))
        return path

    monkeypatch.setattr(merge_excel_module, "extract_excel_file", fake_extract)
    monkeypatch.setattr(merge_excel_module, "write_excel_merge", fake_write)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.xlsx",
        output_stem="merged",
        exclude=ExcludeConfig(),
        kind="excel-merge",
    )

    result = merge_excel(request)

    assert result.item_count == 2
    assert [path.name for path in result.output_paths] == [
        "merged_\u6570\u5f0f_\u30de\u30fc\u30b8.xlsx",
        "\u6a5f\u5bc6_merged_\u6570\u5f0f_\u30de\u30fc\u30b8.xlsx",
        "merged_\u6570\u5f0f_\u30de\u30fc\u30b8.json",
        "\u6a5f\u5bc6_merged_\u6570\u5f0f_\u30de\u30fc\u30b8.json",
        "merged_\u5024_\u30de\u30fc\u30b8.xlsx",
        "\u6a5f\u5bc6_merged_\u5024_\u30de\u30fc\u30b8.xlsx",
        "merged_\u5024_\u30de\u30fc\u30b8.json",
        "\u6a5f\u5bc6_merged_\u5024_\u30de\u30fc\u30b8.json",
    ]
    assert written[0][2][0]["relative_path"] == "normal.xlsx"
    assert written[1][2][0]["relative_path"] == "first-sheet-marker.xlsm"
    assert written[0][3] == "formula"
    assert written[2][3] == "value"
    assert "Classification: sensitive" in written[1][1]
