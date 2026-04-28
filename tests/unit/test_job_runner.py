from pathlib import Path

from file_merge_tool.api.schemas.requests import JobCreateRequest
from file_merge_tool.api.services.job_runner import _build_request, _classification_for_path
from file_merge_tool.domain.merge_job import MergeKind


def test_classification_for_sensitive_output_name() -> None:
    assert _classification_for_path(Path("\u6a5f\u5bc6_images_\u30de\u30fc\u30b8.html")) == "sensitive"
    assert _classification_for_path(Path("images.html")) == "normal"


def test_build_request_ignores_selected_extensions_for_file_list(tmp_path: Path) -> None:
    payload = JobCreateRequest(
        kind=MergeKind.FILE_LIST,
        root_path=tmp_path / "root",
        output_name="file-list.json",
        exclude_extensions=[".log"],
        selected_extensions=[".txt"],
        additional_extensions=[".cfg"],
    )

    request = _build_request(
        payload=payload,
        output_dir=tmp_path / "out",
        output_folder_name="list-run",
    )

    assert request.exclude.extensions == (".log",)
    assert request.selected_extensions == ()
    assert request.additional_extensions == ()


def test_build_request_ignores_exclude_extensions_for_merge_jobs(tmp_path: Path) -> None:
    payload = JobCreateRequest(
        kind=MergeKind.TEXT_MERGE,
        root_path=tmp_path / "root",
        output_name="text.json",
        exclude_extensions=[".md"],
        selected_extensions=[".txt"],
        additional_extensions=[".cfg"],
    )

    request = _build_request(
        payload=payload,
        output_dir=tmp_path / "out",
        output_folder_name="text-run",
    )

    assert request.exclude.extensions == ()
    assert request.selected_extensions == (".txt",)
    assert request.additional_extensions == (".cfg",)
