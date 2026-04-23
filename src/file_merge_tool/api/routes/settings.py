from __future__ import annotations

from fastapi import APIRouter, HTTPException

from file_merge_tool.infrastructure.settings_store import (
    delete_preset,
    load_global_settings,
    load_presets,
    save_global_settings,
    save_preset,
)


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/presets")
def presets() -> dict[str, object]:
    return {"items": load_presets()}


@router.post("/presets")
def upsert_preset(payload: dict[str, object]) -> dict[str, object]:
    try:
        items = save_preset(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"items": items}


@router.delete("/presets/{name}")
def remove_preset(name: str) -> dict[str, object]:
    return {"items": delete_preset(name)}


@router.get("/global")
def global_settings() -> dict[str, object]:
    return load_global_settings()


@router.put("/global")
def put_global_settings(payload: dict[str, object]) -> dict[str, object]:
    return save_global_settings(payload)
