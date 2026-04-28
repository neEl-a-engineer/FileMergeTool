from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _first_existing_dir(repo_root: Path, *candidates: str) -> str:
    for candidate in candidates:
        if (repo_root / candidate).exists():
            return candidate
    return candidates[0]


def _scripts_dir_name(repo_root: Path | None = None) -> str:
    return _first_existing_dir(repo_root or _repo_root(), "40_scripts", "scripts")


def _tests_dir_name(repo_root: Path | None = None) -> str:
    return _first_existing_dir(repo_root or _repo_root(), "30_tests", "tests")


def _optional_script_path(script_name: str) -> Path | None:
    repo_root = _repo_root()
    for scripts_dir_name in ("40_scripts", "scripts"):
        candidate = repo_root / scripts_dir_name / script_name
        if candidate.exists():
            return candidate
    return None


def _run_script(script_path: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    if POWERSHELL is None:
        pytest.skip("PowerShell is not available")

    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), *args],
        cwd=str(cwd or script_path.parent),
        text=True,
        capture_output=True,
        check=False,
    )


def _write_config(project_root: Path, *, history_range: str = "", release_target: str = "80_workspace/public_release/") -> Path:
    config = {
        "global_skip_paths": [".git/", ".venv/"],
        "content_skip_extensions": [".png", ".jpg", ".zip"],
        "global_error_filenames": [".env", "*.pem", "*.key"],
        "content_allow_paths": [],
        "content_allow_patterns": [],
        "content_error_patterns": [
            {
                "name": "generic secret assignment",
                "pattern": r"(?i)\b(api[_-]?key|access[_-]?token|token|secret|password)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}",
            }
        ],
        "content_warning_patterns": [
            {
                "name": "generic email address",
                "pattern": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            }
        ],
        "push": {
            "prefer_upstream_unpushed_range": True,
            "scan_additional_paths": [],
            "fallback_history_range": history_range,
            "blocked_extensions": [".zip", ".pdf", ".docx", ".xlsx", ".pptx"],
            "blocked_extension_allow_paths": [{"path": "80_workspace/public_release/*.zip", "reason": "local export bundle"}],
        },
        "release": {"scan_targets": [release_target]},
        "history": {"scan_range": "--all"},
    }
    config_path = project_root / "sensitive-scan.config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path


def test_release_mode_fails_on_secret_in_bundle(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    export_root = project_root / "80_workspace" / "public_release" / "bundle"
    export_root.mkdir(parents=True)
    secret_line = '{} = "{}"'.format("token", "supersecret123")
    (export_root / "README.md").write_text(secret_line, encoding="utf-8")

    config_path = _write_config(project_root)
    repo_root = _repo_root()
    script_path = repo_root / _scripts_dir_name(repo_root) / "check-sensitive-data.ps1"

    result = _run_script(
        script_path,
        "-Mode",
        "release",
        "-ProjectRoot",
        str(project_root),
        "-ConfigPath",
        str(config_path),
        "-TargetPath",
        str(export_root),
    )

    assert result.returncode == 1
    assert "generic secret assignment" in result.stdout


def test_push_mode_fails_on_staged_secret(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)

    (project_root / "README.md").write_text("safe\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    config_path = _write_config(project_root, history_range="")
    secret_line = '{} = "{}"'.format("password", "supersecret123")
    (project_root / "config.txt").write_text(secret_line, encoding="utf-8")
    subprocess.run(["git", "add", "config.txt"], cwd=project_root, check=True)

    repo_root = _repo_root()
    script_path = repo_root / _scripts_dir_name(repo_root) / "check-sensitive-data.ps1"
    result = _run_script(
        script_path,
        "-Mode",
        "push",
        "-ProjectRoot",
        str(project_root),
        "-ConfigPath",
        str(config_path),
    )

    assert result.returncode == 1
    assert "generic secret assignment" in result.stdout


def test_push_mode_fails_on_unpushed_committed_secret(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)

    (project_root / "README.md").write_text("safe\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    remote_root = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_root)], cwd=project_root, check=True)
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=project_root, check=True, capture_output=True, text=True)

    config_path = _write_config(project_root, history_range="")
    secret_line = '{} = "{}"'.format("access_token", "supersecret123")
    (project_root / "local-only.txt").write_text(secret_line, encoding="utf-8")
    subprocess.run(["git", "add", "local-only.txt"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-m", "local only secret"], cwd=project_root, check=True, capture_output=True, text=True)

    repo_root = _repo_root()
    script_path = repo_root / _scripts_dir_name(repo_root) / "check-sensitive-data.ps1"
    result = _run_script(
        script_path,
        "-Mode",
        "push",
        "-ProjectRoot",
        str(project_root),
        "-ConfigPath",
        str(config_path),
    )

    assert result.returncode == 1
    assert "generic secret assignment" in result.stdout
    assert "push-unpushed-history" in result.stdout


def test_push_mode_fails_on_disallowed_extension(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)

    (project_root / "README.md").write_text("safe\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    config_path = _write_config(project_root, history_range="")
    (project_root / "report.pdf").write_text("not a real pdf but enough for filename policy\n", encoding="utf-8")
    subprocess.run(["git", "add", "report.pdf"], cwd=project_root, check=True)

    repo_root = _repo_root()
    script_path = repo_root / _scripts_dir_name(repo_root) / "check-sensitive-data.ps1"
    result = _run_script(
        script_path,
        "-Mode",
        "push",
        "-ProjectRoot",
        str(project_root),
        "-ConfigPath",
        str(config_path),
    )

    assert result.returncode == 1
    assert "disallowed push extension" in result.stdout


def test_install_git_hooks_sets_core_hooks_path(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    hooks_dir = project_root / ".githooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-push").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    repo_root = _repo_root()
    script_path = repo_root / _scripts_dir_name(repo_root) / "install-git-hooks.ps1"
    result = _run_script(
        script_path,
        "-ProjectRoot",
        str(project_root),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    hooks_path = subprocess.run(
        ["git", "config", "--local", "--get", "core.hooksPath"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert hooks_path == ".githooks"


def test_pre_push_hook_blocks_disallowed_extension_push(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)

    repo_root = _repo_root()
    scripts_dir_name = _scripts_dir_name(repo_root)
    scripts_dir = project_root / scripts_dir_name
    scripts_dir.mkdir()
    hooks_dir = project_root / ".githooks"
    hooks_dir.mkdir()

    shutil.copy2(repo_root / scripts_dir_name / "check-sensitive-data.ps1", scripts_dir / "check-sensitive-data.ps1")
    shutil.copy2(repo_root / ".githooks" / "pre-push", hooks_dir / "pre-push")

    config_path = _write_config(project_root, history_range="HEAD~5..HEAD")
    install_script = repo_root / scripts_dir_name / "install-git-hooks.ps1"
    install_result = _run_script(
        install_script,
        "-ProjectRoot",
        str(project_root),
    )
    assert install_result.returncode == 0, install_result.stdout + install_result.stderr

    (project_root / "README.md").write_text("safe\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md", config_path.name, ".githooks/pre-push", f"{scripts_dir_name}/check-sensitive-data.ps1"],
        cwd=project_root,
        check=True,
    )
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    remote_root = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_root)], cwd=project_root, check=True)
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=project_root, check=True, capture_output=True, text=True)

    (project_root / "report.pdf").write_text("not a real pdf\n", encoding="utf-8")
    subprocess.run(["git", "add", "report.pdf"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-m", "add disallowed file"], cwd=project_root, check=True, capture_output=True, text=True)

    result = subprocess.run(
        ["git", "push", "origin", "HEAD"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    combined_output = result.stdout + result.stderr
    assert "disallowed push extension" in combined_output


def test_export_public_runs_sensitive_check_and_copies_assets(tmp_path: Path) -> None:
    repo_root = _repo_root()
    script_path = _optional_script_path("export-public.ps1")
    if script_path is None:
        pytest.skip("export-public.ps1 is not bundled in this repository layout")
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version = "(.+)"$', pyproject_text, re.MULTILINE)
    assert version_match is not None
    version = version_match.group(1)

    output_root = tmp_path / "public_release"
    result = _run_script(
        script_path,
        "-OutputRoot",
        str(output_root),
        "-SkipZip",
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Running sensitive data check against export" in result.stdout

    export_root = output_root / f"file-merge-tool-public-v{version}"
    assert (export_root / "scripts" / "check-sensitive-data.ps1").exists()
    assert (export_root / "scripts" / "install-git-hooks.ps1").exists()
    assert (export_root / "sensitive-scan.config.json").exists()
    assert (export_root / ".githooks" / "pre-push").exists()
    assert (export_root / "LICENSE").exists()
    assert "MIT License" in (export_root / "LICENSE").read_text(encoding="utf-8")
    assert "Private development repository" not in (export_root / "README.md").read_text(encoding="utf-8")
    assert "Local web and CLI tool" in (export_root / "README.md").read_text(encoding="utf-8")
    assert 'license = { text = "MIT" }' not in pyproject_text
    assert 'license = { text = "MIT" }' in (export_root / "pyproject.toml").read_text(encoding="utf-8")


def test_export_public_skips_generated_python_artifacts_on_copy(tmp_path: Path) -> None:
    repo_root = _repo_root()
    export_script = _optional_script_path("export-public.ps1")
    if export_script is None:
        pytest.skip("export-public.ps1 is not bundled in this repository layout")
    project_root = tmp_path / "project"
    script_dir = project_root / "40_scripts"
    script_dir.mkdir(parents=True)

    shutil.copy2(export_script, script_dir / "export-public.ps1")

    public_scripts = [
        "build-exe-launcher.ps1",
        "check-sensitive-data.ps1",
        "ensure-venv.ps1",
        "install-git-hooks.ps1",
        "merge-file-list.ps1",
        "merge-text.ps1",
        "run-cli.ps1",
        "run-dev.ps1",
        "run-tests.ps1",
        "setup-dev.ps1",
    ]
    for script_name in public_scripts:
        (script_dir / script_name).write_text("# placeholder\n", encoding="utf-8")

    (project_root / "README.public.md").write_text("# Public README\n", encoding="utf-8")
    public_license = project_root / "50_tools" / "public_bundle_assets"
    public_license.mkdir(parents=True)
    (public_license / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    (project_root / ".github" / "workflows").mkdir(parents=True)
    (project_root / ".github" / "workflows" / "tests.yml").write_text("name: tests\n", encoding="utf-8")
    (project_root / ".githooks").mkdir()
    (project_root / ".githooks" / "pre-push").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    src_root = project_root / "20_src"
    src_root.mkdir()
    (src_root / "package.py").write_text("print('ok')\n", encoding="utf-8")
    (src_root / "__pycache__").mkdir()
    (src_root / "__pycache__" / "package.cpython-310.pyc").write_bytes(b"pyc")
    (src_root / "demo.egg-info").mkdir()
    (src_root / "demo.egg-info" / "PKG-INFO").write_text("metadata\n", encoding="utf-8")

    tests_root = project_root / "30_tests"
    tests_root.mkdir()
    (tests_root / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
    (tests_root / ".pytest_cache").mkdir()
    (tests_root / ".pytest_cache" / "cache.txt").write_text("cached\n", encoding="utf-8")

    pyproject_text = """
[project]
name = "demo"
version = "9.9.9"
readme = "README.md"

[tool.setuptools.packages.find]
where = ["20_src"]

[tool.pytest.ini_options]
testpaths = ["30_tests"]
pythonpath = ["20_src"]
""".strip()
    (project_root / "pyproject.toml").write_text(pyproject_text + "\n", encoding="utf-8")

    result = _run_script(
        script_dir / "export-public.ps1",
        "-SkipZip",
        "-SkipSampleConfigs",
        "-SkipSensitiveCheck",
        cwd=project_root,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    export_root = project_root / "80_workspace" / "public_release" / "file-merge-tool-public-v9.9.9"
    assert (export_root / "src" / "package.py").exists()
    assert (export_root / "tests" / "test_smoke.py").exists()
    assert not any(path.name == "__pycache__" for path in export_root.rglob("*"))
    assert not any(path.name == ".pytest_cache" for path in export_root.rglob("*"))
    assert not any(path.name.endswith(".egg-info") for path in export_root.rglob("*"))
    assert not any(path.suffix in {".pyc", ".pyo"} for path in export_root.rglob("*") if path.is_file())
