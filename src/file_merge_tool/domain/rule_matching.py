from __future__ import annotations

import re
from collections.abc import Iterable


def exact_literal_match(value: str, literals: Iterable[str]) -> bool:
    return any(value == literal for literal in literals if literal)


def regex_search_match(value: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, value) for pattern in patterns if pattern)


def matched_literal_substrings(
    haystacks: Iterable[str],
    literals: Iterable[str],
) -> list[str]:
    values = [haystack for haystack in haystacks if haystack]
    matches: list[str] = []
    for literal in literals:
        if literal and any(literal in haystack for haystack in values):
            matches.append(literal)
    return matches


def matched_regex_patterns(
    haystacks: Iterable[str],
    patterns: Iterable[str],
) -> list[str]:
    values = [haystack for haystack in haystacks if haystack]
    matches: list[str] = []
    for pattern in patterns:
        if pattern and any(re.search(pattern, haystack) for haystack in values):
            matches.append(pattern)
    return matches
