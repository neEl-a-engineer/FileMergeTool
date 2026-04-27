from __future__ import annotations

from file_merge_tool.infrastructure.settings_store import delete_preset, load_presets, save_preset


def test_save_preset_adds_index_when_name_already_exists(tmp_path):
    payload = {
        "name": "daily run",
        "kind": "text-merge",
        "outputFolderName": "daily",
        "rootPath": "D:\\Docs",
    }

    items = save_preset(payload, project_root=tmp_path)
    assert items[0]["name"] == "daily run"

    items = save_preset(payload, project_root=tmp_path)
    assert items[0]["name"] == "daily run (2)"
    assert items[1]["name"] == "daily run"

    items = save_preset(payload, project_root=tmp_path)
    assert items[0]["name"] == "daily run (3)"
    assert [item["name"] for item in items[:3]] == ["daily run (3)", "daily run (2)", "daily run"]


def test_delete_preset_removes_only_target_name(tmp_path):
    base = {
        "kind": "text-merge",
        "outputFolderName": "daily",
        "rootPath": "D:\\Docs",
    }
    save_preset({**base, "name": "daily run"}, project_root=tmp_path)
    save_preset({**base, "name": "daily run"}, project_root=tmp_path)

    remaining = delete_preset("daily run (2)", project_root=tmp_path)

    assert [item["name"] for item in remaining] == ["daily run"]
    assert [item["name"] for item in load_presets(project_root=tmp_path)] == ["daily run"]
