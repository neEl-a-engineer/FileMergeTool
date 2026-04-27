from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from file_merge_tool.domain.output_naming import normalize_output_folder_name
from file_merge_tool.infrastructure.output_metadata import build_output_record


HISTORY_LIMIT = 50


def workspace_root(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    return project_root / "80_workspace"


def history_root(project_root: Path | None = None) -> Path:
    return workspace_root(project_root) / "history"


def make_history_dir(
    kind: str,
    job_id: str,
    output_folder_name: str,
    project_root: Path | None = None,
) -> Path:
    del kind, job_id
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    folder_name = normalize_output_folder_name(output_folder_name, default_name="output")
    path = history_root(project_root) / f"{timestamp}_{folder_name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path(run_dir: Path) -> Path:
    return run_dir / "manifest.json"


def write_manifest(run_dir: Path, manifest: dict[str, Any]) -> Path:
    path = manifest_path(run_dir)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    rebuild_history_index()
    trim_history()
    return path


def read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    outputs = manifest.get("outputs")
    if isinstance(outputs, list):
        manifest["outputs"] = [_normalize_output_entry(item) for item in outputs]
    return manifest


def list_history(
    project_root: Path | None = None,
    *,
    include_internal: bool = False,
) -> list[dict[str, Any]]:
    root = history_root(project_root)
    if not root.exists():
        return []

    records: list[dict[str, Any]] = []
    manifest_paths = list(root.glob("*/manifest.json")) + list(root.glob("*/*/manifest.json"))
    for path in manifest_paths:
        manifest = read_manifest(path)
        if manifest is None:
            continue
        if include_internal:
            manifest["_manifest_path"] = str(path)
            manifest["_run_dir"] = str(path.parent)
        records.append(manifest)

    return sorted(records, key=lambda item: item.get("started_at", ""), reverse=True)


def find_history_by_job_id(job_id: str, project_root: Path | None = None) -> dict[str, Any] | None:
    for item in list_history(project_root):
        if item.get("job_id") == job_id:
            return item
    return None


def rebuild_history_index(project_root: Path | None = None) -> Path:
    root = history_root(project_root)
    root.mkdir(parents=True, exist_ok=True)
    records = list_history(project_root)
    index_path = root / "index.json"
    index_path.write_text(
        json.dumps({"schema": "file-merge-tool/history-index/v1", "items": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    return index_path


def trim_history(limit: int = HISTORY_LIMIT, project_root: Path | None = None) -> None:
    records = list_history(project_root, include_internal=True)
    for record in records[limit:]:
        run_dir_value = record.get("_run_dir")
        if not run_dir_value:
            continue
        run_dir = Path(run_dir_value)
        if not run_dir.exists():
            continue
        root = history_root(project_root)
        if run_dir.parent == root or run_dir.parent.parent == root:
            shutil.rmtree(run_dir, ignore_errors=True)
    rebuild_history_index(project_root)


def _normalize_output_entry(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    path_value = value.get("path")
    if not isinstance(path_value, str) or not path_value:
        return dict(value)
    normalized = build_output_record(Path(path_value))
    normalized.update({key: item for key, item in value.items() if key not in normalized})
    return normalized
