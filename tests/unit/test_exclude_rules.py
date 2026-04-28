from pathlib import Path

from file_merge_tool.domain.config import ExcludeConfig
from file_merge_tool.scanning.exclude_rules import ExcludeRules


def test_exclude_config_normalizes_extensions() -> None:
    config = ExcludeConfig.from_iterables([".git"], ["png", ".JPG", ""])

    assert config.extensions == (".png", ".JPG")


def test_exclude_rules_match_folder_case_sensitive() -> None:
    config = ExcludeConfig.from_iterables(["Node_Modules"], [])
    rules = ExcludeRules.from_config(config)

    assert "Node_Modules" in rules.folder_names


def test_exclude_rules_match_folder_regex_case_sensitive() -> None:
    config = ExcludeConfig.from_iterables(folder_patterns=[r"^Build\d+$"])
    rules = ExcludeRules.from_config(config)

    assert rules.folder_reason(Path("Build42")) == "excluded_folder_pattern"
    assert rules.folder_reason(Path("build42")) is None


def test_exclude_rules_match_file_regex_case_sensitive() -> None:
    config = ExcludeConfig.from_iterables(file_patterns=[r"^~\$.*"])
    rules = ExcludeRules.from_config(config)

    assert rules.file_reason(Path("~$draft.docx")) == "excluded_file_pattern"
    assert rules.file_reason(Path("~$Draft.DOCX")) == "excluded_file_pattern"
    assert rules.file_reason(Path("Draft.docx")) is None
