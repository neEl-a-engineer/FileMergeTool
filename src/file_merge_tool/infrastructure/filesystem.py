from __future__ import annotations

from pathlib import Path


def default_output_dir(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    return project_root / "80_workspace" / "outputs"


def ensure_safe_output_name(output_name: str, default_name: str) -> str:
    name = output_name.strip() if output_name else default_name
    if not name:
        name = default_name
    if Path(name).name != name:
        raise ValueError("Output name must be a file name, not a path.")
    return name

