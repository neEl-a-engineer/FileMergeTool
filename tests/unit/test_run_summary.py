from pathlib import Path

from file_merge_tool.application.run_summary import build_run_summary_payload
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.result import FileResult, MergeResult


def test_run_summary_includes_extension_and_error_details(tmp_path: Path) -> None:
    request = MergeRequest(
        root_path=tmp_path / "root",
        output_dir=tmp_path / "out",
        output_name="merged.json",
        output_folder_name="test-run",
        kind="text-merge",
        exclude=ExcludeConfig.from_iterables(
            folder_names=[".git"],
            file_names=["Thumbs.db"],
            folder_patterns=[r"^Build\d+$"],
            file_patterns=[r"^~\$.*"],
        ),
        selected_extensions=(".txt", ".md"),
        additional_extensions=(".cfg",),
        sensitivity_markers=("機密",),
        sensitivity_patterns=(r"CONFIDENTIAL",),
    )
    result = MergeResult(
        output_paths=(),
        item_count=1,
        skipped_count=2,
        excluded_count=1,
        error_skipped_count=1,
        file_results=(
            FileResult(
                relative_path="ok.txt",
                source_path=str(tmp_path / "root" / "ok.txt"),
                status="merged",
                classification="normal",
            ),
            FileResult(
                relative_path="skip.md",
                source_path=str(tmp_path / "root" / "skip.md"),
                status="skipped",
                skip_reason="extension_not_selected",
                details="The file extension is not selected for this merge run.",
            ),
            FileResult(
                relative_path="broken.txt",
                source_path=str(tmp_path / "root" / "broken.txt"),
                status="error",
                skip_reason="read_error",
                exception_type="OSError",
                message="The text file could not be read.",
                details="boom",
            ),
        ),
    )

    payload = build_run_summary_payload(
        request=request,
        status="completed_with_errors",
        started_at="2026-04-28T10:00:00+09:00",
        finished_at="2026-04-28T10:00:02+09:00",
        history_dir=tmp_path / "history",
        outputs=[{"file_name": "test-run_マージ.json"}],
        result=result,
        warnings=["broken.txt: read_error"],
        error=None,
    )

    assert payload["settings"]["selected_extensions"] == [".txt", ".md"]
    assert payload["settings"]["additional_extensions"] == [".cfg"]
    assert payload["settings"]["effective_extensions"] == [".txt", ".md", ".cfg"]
    assert payload["settings"]["exclude_folder_patterns"] == [r"^Build\d+$"]
    assert payload["settings"]["exclude_file_patterns"] == [r"^~\$.*"]
    assert payload["settings"]["sensitivity_patterns"] == [r"CONFIDENTIAL"]
    assert payload["summary"]["merged_file_count"] == 1
    assert payload["summary"]["skipped_file_count"] == 1
    assert payload["summary"]["error_file_count"] == 1
    assert payload["files"][1]["skip_reason"] == "extension_not_selected"
    assert payload["errors"][0]["exception_type"] == "OSError"
