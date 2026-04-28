from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from file_merge_tool.domain.config import ExcludeConfig
from file_merge_tool.domain.extension_selection import path_extension_token
from file_merge_tool.domain.rule_matching import exact_literal_match, regex_search_match


@dataclass(frozen=True)
class ExcludeRules:
    folder_names: frozenset[str]
    extensions: frozenset[str]
    folder_patterns: tuple[str, ...]
    file_names: frozenset[str]
    file_patterns: tuple[str, ...]

    @classmethod
    def from_config(cls, config: ExcludeConfig) -> "ExcludeRules":
        return cls(
            folder_names=frozenset(config.folder_names),
            extensions=frozenset(config.extensions),
            folder_patterns=tuple(config.folder_patterns),
            file_names=frozenset(config.file_names),
            file_patterns=tuple(config.file_patterns),
        )

    def folder_reason(self, path: Path) -> str | None:
        if exact_literal_match(path.name, self.folder_names):
            return "excluded_folder"
        if regex_search_match(path.name, self.folder_patterns):
            return "excluded_folder_pattern"
        return None

    def file_reason(self, path: Path) -> str | None:
        if exact_literal_match(path.name, self.file_names):
            return "excluded_file_name"
        if path_extension_token(path) in self.extensions:
            return "excluded_extension"
        if regex_search_match(path.name, self.file_patterns):
            return "excluded_file_pattern"
        return None
