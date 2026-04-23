from __future__ import annotations

import json
from pathlib import Path

from file_merge_tool.infrastructure.history import list_history, trim_history


def test_trim_history_keeps_newest_50_runs(tmp_path: Path) -> None:
    history_root = tmp_path / "80_workspace" / "history" / "file-list"
    for index in range(51):
        run_dir = history_root / f"20260423-22{index:02d}00_job{index:02d}"
        run_dir.mkdir(parents=True)
        manifest = {
            "schema": "file-merge-tool/history-manifest/v1",
            "job_id": f"job-{index:02d}",
            "kind": "file-list",
            "status": "completed",
            "started_at": f"2026-04-23T22:{index:02d}:00+09:00",
            "finished_at": f"2026-04-23T22:{index:02d}:01+09:00",
            "outputs": [],
            "summary": {},
            "warnings": [],
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False),
            encoding="utf-8",
        )

    trim_history(project_root=tmp_path)
    records = list_history(project_root=tmp_path)

    assert len(records) == 50
    assert all(record["job_id"] != "job-00" for record in records)
    assert records[0]["job_id"] == "job-50"
