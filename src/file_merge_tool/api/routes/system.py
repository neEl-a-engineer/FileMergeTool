from __future__ import annotations

from fastapi import APIRouter

from file_merge_tool.api.services.restart_server import schedule_server_restart


router = APIRouter(prefix="/api/system", tags=["system"])


@router.post("/restart")
def restart_server() -> dict[str, object]:
    return schedule_server_restart()
