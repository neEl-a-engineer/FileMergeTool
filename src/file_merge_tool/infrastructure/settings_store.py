from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from file_merge_tool.infrastructure.history import workspace_root


def settings_dir(project_root: Path | None = None) -> Path:
    path = workspace_root(project_root) / "settings"
    path.mkdir(parents=True, exist_ok=True)
    return path


def presets_path(project_root: Path | None = None) -> Path:
    return settings_dir(project_root) / "presets.json"


def global_settings_path(project_root: Path | None = None) -> Path:
    return settings_dir(project_root) / "global-settings.json"


def load_presets(project_root: Path | None = None) -> list[dict[str, Any]]:
    path = presets_path(project_root)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def save_preset(preset: dict[str, Any], project_root: Path | None = None) -> list[dict[str, Any]]:
    name = str(preset.get("name", "")).strip()
    if not name:
        raise ValueError("Preset name is required.")
    presets = load_presets(project_root)
    unique_name = _next_preset_name(name, presets)
    presets.insert(0, {**preset, "name": unique_name})
    _write_json(presets_path(project_root), presets)
    return presets


def delete_preset(name: str, project_root: Path | None = None) -> list[dict[str, Any]]:
    presets = [item for item in load_presets(project_root) if item.get("name") != name]
    _write_json(presets_path(project_root), presets)
    return presets


def load_global_settings(project_root: Path | None = None) -> dict[str, Any]:
    path = global_settings_path(project_root)
    if not path.exists():
        return {"language": "ja", "globalMarkers": ["機密", "極秘"]}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"language": "ja", "globalMarkers": ["機密", "極秘"]}
    return value if isinstance(value, dict) else {"language": "ja", "globalMarkers": ["機密", "極秘"]}


def save_global_settings(settings: dict[str, Any], project_root: Path | None = None) -> dict[str, Any]:
    _write_json(global_settings_path(project_root), settings)
    return settings


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def _next_preset_name(requested_name: str, presets: list[dict[str, Any]]) -> str:
    existing_names = {
        str(item.get("name", "")).strip()
        for item in presets
        if str(item.get("name", "")).strip()
    }
    if requested_name not in existing_names:
        return requested_name
    index = 2
    while f"{requested_name} ({index})" in existing_names:
        index += 1
    return f"{requested_name} ({index})"
