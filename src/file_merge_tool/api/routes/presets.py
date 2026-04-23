from __future__ import annotations

from fastapi import APIRouter

from file_merge_tool.domain.merge_job import MergeKind


router = APIRouter(prefix="/api")


@router.get("/presets")
def presets() -> dict[str, object]:
    return {
        "kinds": [kind.value for kind in MergeKind],
        "implemented_kinds": [MergeKind.FILE_LIST.value, MergeKind.TEXT_MERGE.value],
        "image_output_formats": ["html", "pptx"],
        "default_exclude_dirs": [".git", ".venv", "__pycache__", "node_modules"],
        "default_exclude_extensions": [".png", ".jpg", ".jpeg", ".gif", ".zip", ".exe", ".dll"],
    }
