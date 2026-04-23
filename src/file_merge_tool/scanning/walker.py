from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from file_merge_tool.domain.config import ExcludeConfig
from file_merge_tool.domain.file_item import ScannedItem
from file_merge_tool.scanning.exclude_rules import ExcludeRules
from file_merge_tool.scanning.timestamps import modified_at_iso


def walk_tree(root_path: Path, exclude: ExcludeConfig) -> Iterator[ScannedItem]:
    root = root_path.resolve()
    rules = ExcludeRules.from_config(exclude)

    if not root.exists():
        raise FileNotFoundError(f"Root path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root}")

    yield ScannedItem(
        absolute_path=root,
        relative_path=".",
        kind="folder",
        modified_at=modified_at_iso(root),
    )
    yield from _walk_children(root, root, rules)


def _walk_children(root: Path, folder: Path, rules: ExcludeRules) -> Iterator[ScannedItem]:
    try:
        children = list(folder.iterdir())
    except OSError as exc:
        yield ScannedItem(
            absolute_path=folder,
            relative_path=_relative_path(root, folder),
            kind="folder",
            modified_at=modified_at_iso(folder),
            excluded=True,
            excluded_reason=f"read_error:{exc.__class__.__name__}",
        )
        return

    files, folders, others = _partition_children(children)

    for child in files:
        reason = rules.file_reason(child)
        yield ScannedItem(
            absolute_path=_safe_resolve(child),
            relative_path=_relative_path(root, child),
            kind="file",
            modified_at=modified_at_iso(child),
            excluded=reason is not None,
            excluded_reason=reason,
        )

    for child in others:
        is_link = child.is_symlink()
        yield ScannedItem(
            absolute_path=child.absolute() if is_link else _safe_resolve(child),
            relative_path=_relative_path(root, child),
            kind="symlink" if is_link else "other",
            modified_at=modified_at_iso(child),
            excluded=True,
            excluded_reason="symlink_not_followed" if is_link else "unsupported_file_type",
            link_target=_link_target(child) if is_link else None,
        )

    for child in folders:
        reason = rules.folder_reason(child)
        yield ScannedItem(
            absolute_path=_safe_resolve(child),
            relative_path=_relative_path(root, child),
            kind="folder",
            modified_at=modified_at_iso(child),
            excluded=reason is not None,
            excluded_reason=reason,
        )
        if reason is None:
            yield from _walk_children(root, child, rules)


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _partition_children(children: list[Path]) -> tuple[list[Path], list[Path], list[Path]]:
    files: list[Path] = []
    folders: list[Path] = []
    others: list[Path] = []

    for child in children:
        if child.is_symlink():
            others.append(child)
        elif child.is_file():
            files.append(child)
        elif child.is_dir():
            folders.append(child)
        else:
            others.append(child)

    key = lambda item: item.name.casefold()
    return sorted(files, key=key), sorted(folders, key=key), sorted(others, key=key)


def _safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _link_target(path: Path) -> str | None:
    try:
        return str(path.readlink())
    except OSError:
        return None
