from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from file_merge_tool.application.output_files import summary_output_path
from file_merge_tool.application.run_summary import build_run_summary_payload, write_run_summary
from file_merge_tool.domain.config import (
    ExcludeConfig,
    MergeRequest,
    normalize_extension_values,
    normalize_literal_values,
    normalize_regex_values,
)
from file_merge_tool.domain.extension_selection import default_selected_extensions
from file_merge_tool.domain.merge_job import MergeKind
from file_merge_tool.infrastructure.output_metadata import build_output_record
from file_merge_tool.infrastructure.filesystem import default_output_dir, ensure_safe_output_name
from file_merge_tool.application.run_job import run_job
from datetime import datetime, timezone


app = typer.Typer(help="Create AI-friendly file merge artifacts.")


def _request(
    root_path: Path,
    output_dir: Path | None,
    output_name: str,
    exclude_dir: list[str],
    exclude_ext: list[str],
    exclude_file: list[str],
    kind: MergeKind,
    output_stem: str | None = None,
    output_folder_name: str | None = None,
    sensitive_marker: list[str] | None = None,
    sensitive_pattern: list[str] | None = None,
    selected_ext: list[str] | None = None,
    additional_ext: list[str] | None = None,
    exclude_dir_pattern: list[str] | None = None,
    exclude_file_pattern: list[str] | None = None,
    image_format: list[str] | None = None,
) -> MergeRequest:
    return MergeRequest(
        root_path=root_path,
        output_dir=output_dir.resolve() if output_dir else default_output_dir(),
        output_name=output_name,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        exclude=ExcludeConfig.from_iterables(
            folder_names=exclude_dir,
            extensions=exclude_ext,
            file_names=exclude_file,
            folder_patterns=exclude_dir_pattern,
            file_patterns=exclude_file_pattern,
        ),
        selected_extensions=tuple(
            normalize_extension_values(selected_ext) or default_selected_extensions(kind.value)
        ),
        additional_extensions=tuple(normalize_extension_values(additional_ext)),
        kind=kind.value,
        sensitivity_markers=tuple(normalize_literal_values(sensitive_marker)),
        sensitivity_patterns=tuple(normalize_regex_values(sensitive_pattern)),
        image_output_formats=tuple(image_format or []),
    )


def _run_and_print(kind: MergeKind, request: MergeRequest) -> None:
    started_at = _now()
    result = run_job(kind, request)
    finished_at = _now()
    output_records = [build_output_record(path) for path in result.output_paths]
    summary_path = summary_output_path(request, default_name=Path(request.output_name).stem or kind.value)
    summary_record = build_output_record(summary_path)
    summary_payload = build_run_summary_payload(
        request=request,
        status="completed",
        started_at=started_at,
        finished_at=finished_at,
        history_dir=request.output_dir,
        outputs=[*output_records, summary_record],
        result=result,
        warnings=list(result.warnings),
        error=None,
    )
    write_run_summary(summary_path, summary_payload)
    for output_path in (*result.output_paths, summary_path):
        typer.echo(str(output_path))


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@app.command("file-list")
def file_list(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "file-list.json",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "file-list.json"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
        kind=MergeKind.FILE_LIST,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
    )
    _run_and_print(MergeKind.FILE_LIST, request)


@app.command("text-merge")
def text_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "text-merge.json",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "text-merge.json"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
        kind=MergeKind.TEXT_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
    )
    _run_and_print(MergeKind.TEXT_MERGE, request)


@app.command("mail-merge")
def mail_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "mail-merge.json",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    sensitive_pattern: Annotated[list[str], typer.Option("--sensitive-regex")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "mail-merge.json"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        kind=MergeKind.MAIL_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        sensitive_marker=sensitive_marker,
        sensitive_pattern=sensitive_pattern,
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
    )
    _run_and_print(MergeKind.MAIL_MERGE, request)


@app.command("powerpoint-merge")
def powerpoint_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.pptx",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    sensitive_pattern: Annotated[list[str], typer.Option("--sensitive-regex")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.pptx"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        kind=MergeKind.POWERPOINT_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        sensitive_marker=sensitive_marker,
        sensitive_pattern=sensitive_pattern,
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
    )
    _run_and_print(MergeKind.POWERPOINT_MERGE, request)


@app.command("excel-merge")
def excel_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.xlsx",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    sensitive_pattern: Annotated[list[str], typer.Option("--sensitive-regex")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.xlsx"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        kind=MergeKind.EXCEL_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        sensitive_marker=sensitive_marker,
        sensitive_pattern=sensitive_pattern,
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
    )
    _run_and_print(MergeKind.EXCEL_MERGE, request)


@app.command("word-merge")
def word_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.docx",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    sensitive_pattern: Annotated[list[str], typer.Option("--sensitive-regex")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.docx"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        kind=MergeKind.WORD_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        sensitive_marker=sensitive_marker,
        sensitive_pattern=sensitive_pattern,
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
    )
    _run_and_print(MergeKind.WORD_MERGE, request)


@app.command("pdf-merge")
def pdf_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.pdf",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    sensitive_pattern: Annotated[list[str], typer.Option("--sensitive-regex")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.pdf"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        kind=MergeKind.PDF_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        sensitive_marker=sensitive_marker,
        sensitive_pattern=sensitive_pattern,
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
    )
    _run_and_print(MergeKind.PDF_MERGE, request)


@app.command("image-merge")
def image_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "images.html",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    output_folder_name: Annotated[str | None, typer.Option("--output-folder-name")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    sensitive_pattern: Annotated[list[str], typer.Option("--sensitive-regex")] = None,
    selected_ext: Annotated[list[str], typer.Option("--select-ext")] = None,
    additional_ext: Annotated[list[str], typer.Option("--add-ext")] = None,
    exclude_dir_pattern: Annotated[list[str], typer.Option("--exclude-dir-regex")] = None,
    exclude_file_pattern: Annotated[list[str], typer.Option("--exclude-file-regex")] = None,
    image_format: Annotated[list[str], typer.Option("--format")] = None,
) -> None:
    formats = image_format or ["html"]
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "images.html"),
        exclude_dir=exclude_dir or [],
        exclude_ext=[],
        exclude_file=exclude_file or [],
        kind=MergeKind.IMAGE_MERGE,
        output_stem=output_stem,
        output_folder_name=output_folder_name,
        sensitive_marker=sensitive_marker,
        sensitive_pattern=sensitive_pattern,
        selected_ext=selected_ext,
        additional_ext=additional_ext,
        exclude_dir_pattern=exclude_dir_pattern or [],
        exclude_file_pattern=exclude_file_pattern or [],
        image_format=formats,
    )
    _run_and_print(MergeKind.IMAGE_MERGE, request)


if __name__ == "__main__":
    app()
