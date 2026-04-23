from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.sensitivity import SENSITIVE_MARKERS


TRAVERSAL_ORDER = "files-first-depth-first-name-asc"


class ExcludeInfo(BaseModel):
    folders: list[str] = Field(default_factory=list)
    extensions: list[str] = Field(default_factory=list)
    file_names: list[str] = Field(default_factory=list)


class TraversalInfo(BaseModel):
    order: str = TRAVERSAL_ORDER
    follow_symlinks: bool = False


class SensitivityInfo(BaseModel):
    default_markers: list[str] = Field(default_factory=list)
    additional_markers: list[str] = Field(default_factory=list)
    split_outputs: bool = True


class ArtifactHeader(BaseModel):
    job_id: str | None = None
    tool: str = "file-merge-tool"
    schema_name: str = Field(alias="schema")
    kind: str
    classification: str = "normal"
    generated_at: str
    source_root: str
    setting_name: str | None = None
    traversal: TraversalInfo = Field(default_factory=TraversalInfo)
    exclude: ExcludeInfo
    sensitivity: SensitivityInfo


class ArtifactSummary(BaseModel):
    item_count: int = 0
    excluded_count: int = 0
    skipped_count: int = 0
    error_skipped_count: int = 0
    warning_count: int = 0


class WarningItem(BaseModel):
    relative_path: str
    reason: str
    message: str
    exception_type: str | None = None


class SkippedItem(BaseModel):
    relative_path: str
    kind: str
    reason: str
    absolute_path: str | None = None
    link_target: str | None = None


def build_artifact_header(
    request: MergeRequest,
    *,
    schema_name: str,
    kind: str,
    classification: str = "normal",
) -> dict[str, Any]:
    default_markers = list(SENSITIVE_MARKERS)
    additional_markers = [
        marker for marker in request.sensitivity_markers if marker not in default_markers
    ]
    header = ArtifactHeader(
        job_id=request.job_id,
        schema=schema_name,
        kind=kind,
        classification=classification,
        generated_at=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        source_root=str(request.root_path.resolve()),
        setting_name=request.setting_name,
        exclude=ExcludeInfo(
            folders=list(request.exclude.folder_names),
            extensions=list(request.exclude.extensions),
            file_names=list(request.exclude.file_names),
        ),
        sensitivity=SensitivityInfo(
            default_markers=default_markers,
            additional_markers=list(additional_markers),
        ),
    )
    return model_to_dict(header, by_alias=True, exclude_none=True)


def model_to_dict(model: BaseModel, **kwargs: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)  # type: ignore[attr-defined]
    return model.dict(**kwargs)
