from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ExcludeConfig:
    folder_names: tuple[str, ...] = ()
    extensions: tuple[str, ...] = ()
    file_names: tuple[str, ...] = ()

    @classmethod
    def from_iterables(
        cls,
        folder_names: list[str] | tuple[str, ...] | None = None,
        extensions: list[str] | tuple[str, ...] | None = None,
        file_names: list[str] | tuple[str, ...] | None = None,
    ) -> "ExcludeConfig":
        normalized_extensions: list[str] = []
        for extension in extensions or ():
            value = extension.strip().lower()
            if not value:
                continue
            normalized_extensions.append(value if value.startswith(".") else f".{value}")

        normalized_folders = tuple(
            folder.strip() for folder in folder_names or () if folder and folder.strip()
        )
        normalized_files = tuple(file.strip() for file in file_names or () if file and file.strip())
        return cls(
            folder_names=normalized_folders,
            extensions=tuple(dict.fromkeys(normalized_extensions)),
            file_names=normalized_files,
        )


@dataclass(frozen=True)
class MergeRequest:
    root_path: Path
    output_dir: Path
    output_name: str
    output_stem: str | None = None
    output_folder_name: str | None = None
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)
    job_id: str | None = None
    kind: str | None = None
    setting_name: str | None = None
    sensitivity_markers: tuple[str, ...] = ()
    image_output_formats: tuple[str, ...] = ()
