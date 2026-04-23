from __future__ import annotations

from fastapi import APIRouter

from file_merge_tool.infrastructure.history import list_history


router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def history_list() -> dict[str, object]:
    return {
        "schema": "file-merge-tool/history-list/v1",
        "items": list_history(),
    }

