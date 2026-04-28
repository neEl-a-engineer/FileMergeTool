from pathlib import Path

from file_merge_tool.application.merge_text import merge_text
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest


def test_text_merge_writes_lines(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("one\ntwo\n", encoding="utf-8")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.json",
        exclude=ExcludeConfig(),
    )

    result = merge_text(request)

    assert result.item_count == 1
    assert result.output_paths[0].exists()


def test_text_merge_skips_unselected_extensions_and_records_reason(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    (root / "b.md").write_text("two\n", encoding="utf-8")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.json",
        kind="text-merge",
        exclude=ExcludeConfig(),
        selected_extensions=(".txt",),
        additional_extensions=(),
    )

    result = merge_text(request)

    assert result.item_count == 1
    assert result.skipped_count == 1
    assert any(
        item.relative_path == "b.md" and item.skip_reason == "extension_not_selected"
        for item in result.file_results
    )


def test_text_merge_excludes_by_file_pattern(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "~$draft.txt").write_text("skip\n", encoding="utf-8")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="merged.json",
        kind="text-merge",
        exclude=ExcludeConfig.from_iterables(file_patterns=[r"^~\$.*"]),
        selected_extensions=(".txt",),
    )

    result = merge_text(request)

    assert result.item_count == 0
    assert result.skipped_count == 1
    assert any(
        item.relative_path == "~$draft.txt" and item.skip_reason == "excluded_file_pattern"
        for item in result.file_results
    )
