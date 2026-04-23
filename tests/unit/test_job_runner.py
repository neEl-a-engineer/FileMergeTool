from pathlib import Path

from file_merge_tool.api.services.job_runner import _classification_for_path


def test_classification_for_sensitive_output_name() -> None:
    assert _classification_for_path(Path("images_\u6a5f\u5bc6.html")) == "sensitive"
    assert _classification_for_path(Path("images.html")) == "normal"
