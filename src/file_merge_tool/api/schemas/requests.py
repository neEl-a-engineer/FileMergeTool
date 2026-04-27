from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from file_merge_tool.domain.merge_job import MergeKind


class JobCreateRequest(BaseModel):
    kind: MergeKind = Field(default=MergeKind.FILE_LIST)
    root_path: Path
    output_dir: Path | None = None
    output_stem: str | None = None
    output_folder_name: str | None = None
    output_name: str | None = None
    setting_name: str | None = None
    image_output_formats: list[str] = Field(default_factory=list)
    exclude_dirs: list[str] = Field(default_factory=list)
    exclude_extensions: list[str] = Field(default_factory=list)
    exclude_files: list[str] = Field(default_factory=list)
    additional_sensitive_markers: list[str] = Field(default_factory=list)
