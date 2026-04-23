from file_merge_tool.domain.config import ExcludeConfig
from file_merge_tool.scanning.exclude_rules import ExcludeRules


def test_exclude_config_normalizes_extensions() -> None:
    config = ExcludeConfig.from_iterables([".git"], ["png", ".JPG", ""])

    assert config.extensions == (".png", ".jpg")


def test_exclude_rules_match_folder_case_insensitive() -> None:
    config = ExcludeConfig.from_iterables(["Node_Modules"], [])
    rules = ExcludeRules.from_config(config)

    assert "node_modules" in rules.folder_names

