from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


def normalize_extension_values(
    values: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    normalized: list[str] = []
    for extension in values or ():
        value = str(extension).strip()
        if not value:
            continue
        normalized.append(value if value.startswith(".") else f".{value}")
    return tuple(dict.fromkeys(normalized))


def normalize_literal_values(
    values: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    return tuple(str(value).strip() for value in values or () if str(value).strip())


def normalize_regex_values(
    values: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    normalized = normalize_literal_values(values)
    for pattern in normalized:
        re.compile(pattern)
    return normalized


@dataclass(frozen=True)
class ExcludeConfig:
    folder_names: tuple[str, ...] = ()
    extensions: tuple[str, ...] = ()
    folder_patterns: tuple[str, ...] = ()
    file_names: tuple[str, ...] = ()
    file_patterns: tuple[str, ...] = ()

    @classmethod
    def from_iterables(
        cls,
        folder_names: list[str] | tuple[str, ...] | None = None,
        extensions: list[str] | tuple[str, ...] | None = None,
        file_names: list[str] | tuple[str, ...] | None = None,
        *,
        folder_patterns: list[str] | tuple[str, ...] | None = None,
        file_patterns: list[str] | tuple[str, ...] | None = None,
    ) -> "ExcludeConfig":
        return cls(
            folder_names=normalize_literal_values(folder_names),
            extensions=normalize_extension_values(extensions),
            folder_patterns=normalize_regex_values(folder_patterns),
            file_names=normalize_literal_values(file_names),
            file_patterns=normalize_regex_values(file_patterns),
        )


@dataclass(frozen=True)
class MergeRequest:
    root_path: Path
    output_dir: Path
    output_name: str
    output_stem: str | None = None
    output_folder_name: str | None = None
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)
    selected_extensions: tuple[str, ...] = ()
    additional_extensions: tuple[str, ...] = ()
    job_id: str | None = None
    kind: str | None = None
    setting_name: str | None = None
    sensitivity_markers: tuple[str, ...] = ()
    sensitivity_patterns: tuple[str, ...] = ()
    image_output_formats: tuple[str, ...] = ()
