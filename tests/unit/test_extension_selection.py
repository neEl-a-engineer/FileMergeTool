from pathlib import Path

from file_merge_tool.domain.extension_selection import (
    default_selected_extensions,
    effective_selected_extensions,
    is_extension_selected,
    path_extension_token,
)


def test_path_extension_token_handles_dotfiles() -> None:
    assert path_extension_token(Path(".env")) == ".env"
    assert path_extension_token(Path(".gitignore")) == ".gitignore"


def test_effective_selected_extensions_keeps_selected_and_additional_separate_order() -> None:
    assert effective_selected_extensions([".txt", "md"], [".cfg", ".txt"]) == (
        ".txt",
        ".md",
        ".cfg",
    )


def test_is_extension_selected_is_case_sensitive() -> None:
    assert is_extension_selected(
        Path("notes.md"),
        selected_extensions=[".md"],
        additional_extensions=[],
        kind="text-merge",
    )


def test_text_merge_defaults_include_programming_and_config_extensions() -> None:
    selected = default_selected_extensions("text-merge")

    assert ".java" in selected
    assert ".c" in selected
    assert ".cs" in selected
    assert ".env" in selected
    assert not is_extension_selected(
        Path("notes.MD"),
        selected_extensions=[".md"],
        additional_extensions=[],
        kind="text-merge",
    )
