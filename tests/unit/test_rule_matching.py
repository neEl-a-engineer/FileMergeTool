from file_merge_tool.domain.rule_matching import (
    matched_literal_substrings,
    matched_regex_patterns,
    regex_search_match,
)


def test_regex_search_match_is_case_sensitive() -> None:
    assert regex_search_match("Build42", [r"^Build\d+$"])
    assert not regex_search_match("build42", [r"^Build\d+$"])


def test_matched_literal_substrings_use_partial_case_sensitive_matching() -> None:
    assert matched_literal_substrings(["機密資料", "summary"], ["機密", "極秘"]) == ["機密"]
    assert matched_literal_substrings(["confidential"], ["CONFIDENTIAL"]) == []


def test_matched_regex_patterns_use_case_sensitive_search() -> None:
    assert matched_regex_patterns(["CONFIDENTIAL plan"], [r"CONFIDENTIAL"]) == [r"CONFIDENTIAL"]
    assert matched_regex_patterns(["confidential plan"], [r"CONFIDENTIAL"]) == []
