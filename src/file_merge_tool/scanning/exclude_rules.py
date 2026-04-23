from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from file_merge_tool.domain.config import ExcludeConfig


@dataclass(frozen=True)
class ExcludeRules:
    folder_names: frozenset[str]
    extensions: frozenset[str]
    file_names: frozenset[str]

    @classmethod
    def from_config(cls, config: ExcludeConfig) -> "ExcludeRules":
        folders = frozenset(folder.casefold() for folder in config.folder_names)
        extensions = frozenset(extension.lower() for extension in config.extensions)
        files = frozenset(file.casefold() for file in config.file_names)
        return cls(folder_names=folders, extensions=extensions, file_names=files)

    def folder_reason(self, path: Path) -> str | None:
        if path.name.casefold() in self.folder_names:
            return "excluded_folder"
        return None

    def file_reason(self, path: Path) -> str | None:
        if path.name.casefold() in self.file_names:
            return "excluded_file_name"
        if path.suffix.lower() in self.extensions:
            return "excluded_extension"
        return None
