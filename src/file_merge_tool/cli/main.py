from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.merge_job import MergeKind
from file_merge_tool.infrastructure.filesystem import default_output_dir, ensure_safe_output_name
from file_merge_tool.application.run_job import run_job


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
    sensitive_marker: list[str] | None = None,
    image_format: list[str] | None = None,
) -> MergeRequest:
    return MergeRequest(
        root_path=root_path,
        output_dir=output_dir.resolve() if output_dir else default_output_dir(),
        output_name=output_name,
        output_stem=output_stem,
        exclude=ExcludeConfig.from_iterables(exclude_dir, exclude_ext, exclude_file),
        kind=kind.value,
        sensitivity_markers=tuple(sensitive_marker or []),
        image_output_formats=tuple(image_format or []),
    )


def _run_and_print(kind: MergeKind, request: MergeRequest) -> None:
    result = run_job(kind, request)
    for output_path in result.output_paths:
        typer.echo(str(output_path))


@app.command("file-list")
def file_list(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "file-list.json",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "file-list.json"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.FILE_LIST,
        output_stem=output_stem,
    )
    _run_and_print(MergeKind.FILE_LIST, request)


@app.command("text-merge")
def text_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "text-merge.json",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "text-merge.json"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.TEXT_MERGE,
        output_stem=output_stem,
    )
    _run_and_print(MergeKind.TEXT_MERGE, request)


@app.command("mail-merge")
def mail_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "mail-merge.json",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "mail-merge.json"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.MAIL_MERGE,
        output_stem=output_stem,
        sensitive_marker=sensitive_marker,
    )
    _run_and_print(MergeKind.MAIL_MERGE, request)


@app.command("powerpoint-merge")
def powerpoint_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.pptx",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.pptx"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.POWERPOINT_MERGE,
        output_stem=output_stem,
        sensitive_marker=sensitive_marker,
    )
    _run_and_print(MergeKind.POWERPOINT_MERGE, request)


@app.command("excel-merge")
def excel_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.xlsx",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.xlsx"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.EXCEL_MERGE,
        output_stem=output_stem,
        sensitive_marker=sensitive_marker,
    )
    _run_and_print(MergeKind.EXCEL_MERGE, request)


@app.command("word-merge")
def word_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.docx",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.docx"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.WORD_MERGE,
        output_stem=output_stem,
        sensitive_marker=sensitive_marker,
    )
    _run_and_print(MergeKind.WORD_MERGE, request)


@app.command("pdf-merge")
def pdf_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "merged.pdf",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
) -> None:
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "merged.pdf"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.PDF_MERGE,
        output_stem=output_stem,
        sensitive_marker=sensitive_marker,
    )
    _run_and_print(MergeKind.PDF_MERGE, request)


@app.command("image-merge")
def image_merge(
    root_path: Annotated[Path, typer.Argument(help="Root folder to scan.")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    output_name: Annotated[str, typer.Option("--output-name", "-o")] = "images.html",
    output_stem: Annotated[str | None, typer.Option("--output-stem")] = None,
    exclude_dir: Annotated[list[str], typer.Option("--exclude-dir")] = None,
    exclude_ext: Annotated[list[str], typer.Option("--exclude-ext")] = None,
    exclude_file: Annotated[list[str], typer.Option("--exclude-file")] = None,
    sensitive_marker: Annotated[list[str], typer.Option("--sensitive-marker")] = None,
    image_format: Annotated[list[str], typer.Option("--format")] = None,
) -> None:
    formats = image_format or ["html"]
    request = _request(
        root_path=root_path,
        output_dir=output_dir,
        output_name=ensure_safe_output_name(output_name, "images.html"),
        exclude_dir=exclude_dir or [],
        exclude_ext=exclude_ext or [],
        exclude_file=exclude_file or [],
        kind=MergeKind.IMAGE_MERGE,
        output_stem=output_stem,
        sensitive_marker=sensitive_marker,
        image_format=formats,
    )
    _run_and_print(MergeKind.IMAGE_MERGE, request)


if __name__ == "__main__":
    app()
