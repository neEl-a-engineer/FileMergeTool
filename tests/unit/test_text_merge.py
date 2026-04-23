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

