from __future__ import annotations

import json
import re
from pathlib import Path

from file_merge_tool.infrastructure.history import list_history, make_history_dir, trim_history
from file_merge_tool.infrastructure.output_metadata import build_output_record


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


def test_make_history_dir_uses_flat_timestamp_and_output_folder_name(tmp_path: Path) -> None:
    run_dir = make_history_dir("text-merge", "job-1234", "テスト", project_root=tmp_path)

    assert run_dir.parent == tmp_path / "80_workspace" / "history"
    assert re.fullmatch(r"\d{8}_\d{6}_テスト", run_dir.name)


def test_build_output_record_sets_category_variant_and_preview_mode() -> None:
    summary = build_output_record(Path("テスト_集計.json"))
    assert summary["category"] == "summary"
    assert summary["preview_mode"] == "json"

    excel = build_output_record(Path("機密_テスト_数式_マージ.xlsx"))
    assert excel["classification"] == "sensitive"
    assert excel["variant"] == "formula"
    assert excel["preview_mode"] == "external"
