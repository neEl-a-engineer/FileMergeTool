from pathlib import Path

from file_merge_tool.application.create_file_list import create_file_list
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest


def test_file_list_includes_excluded_folder(tmp_path: Path) -> None:
    root = tmp_path / "root"
    ignored = root / "ignored"
    ignored.mkdir(parents=True)
    (ignored / "hidden.txt").write_text("hidden", encoding="utf-8")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="file-list.json",
        exclude=ExcludeConfig.from_iterables(["ignored"], []),
    )

    result = create_file_list(request)

    output = result.output_paths[0].read_text(encoding="utf-8")
    assert '"relative_path": "ignored"' in output
    assert '"excluded_reason": "excluded_folder"' in output
    assert "hidden.txt" not in output


def test_file_list_marks_excluded_file_name(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "desktop.ini").write_text("metadata", encoding="utf-8")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="file-list.json",
        exclude=ExcludeConfig.from_iterables([], [], ["desktop.ini"]),
    )

    result = create_file_list(request)

    output = result.output_paths[0].read_text(encoding="utf-8")
    assert '"relative_path": "desktop.ini"' in output
    assert '"excluded_reason": "excluded_file_name"' in output


def test_file_list_uses_files_first_depth_first_order(tmp_path: Path) -> None:
    root = tmp_path / "root"
    child = root / "child"
    child.mkdir(parents=True)
    (root / "b.txt").write_text("b", encoding="utf-8")
    (root / "a.txt").write_text("a", encoding="utf-8")
    (child / "c.txt").write_text("c", encoding="utf-8")

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="file-list.json",
        exclude=ExcludeConfig(),
    )

    create_file_list(request)
    output = (tmp_path / "out" / "file-list.json").read_text(encoding="utf-8")

    assert output.index('"relative_path": "a.txt"') < output.index('"relative_path": "b.txt"')
    assert output.index('"relative_path": "b.txt"') < output.index('"relative_path": "child"')
    assert output.index('"relative_path": "child"') < output.index('"relative_path": "child/c.txt"')


def test_file_list_records_symlink_without_following(tmp_path: Path) -> None:
    root = tmp_path / "root"
    target = tmp_path / "target"
    root.mkdir()
    target.mkdir()
    (target / "hidden.txt").write_text("hidden", encoding="utf-8")
    link = root / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        return

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="file-list.json",
        exclude=ExcludeConfig(),
    )

    create_file_list(request)
    output = (tmp_path / "out" / "file-list.json").read_text(encoding="utf-8")

    assert '"kind": "symlink"' in output
    assert '"excluded_reason": "symlink_not_followed"' in output
    assert "hidden.txt" not in output
