from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.infrastructure.office_com.office_app import require_pywin32


WD_FORMAT_XML_DOCUMENT = 16
WD_PAGE_BREAK = 7
WD_STATISTIC_PAGES = 2


class WordApp:
    def __enter__(self) -> "WordApp":
        require_pywin32()
        import win32com.client  # type: ignore[import-not-found]

        self.app = win32com.client.DispatchEx("Word.Application")
        self.app.Visible = False
        self.app.DisplayAlerts = 0
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        quit_app = getattr(self.app, "Quit", None)
        if callable(quit_app):
            quit_app()


def read_word_info(path: Path) -> dict[str, Any]:
    with WordApp() as session:
        document = session.app.Documents.Open(
            str(path.resolve()),
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
        )
        try:
            text = str(document.Content.Text or "").strip()
            return {
                "page_count": int(document.ComputeStatistics(WD_STATISTIC_PAGES)),
                "leading_text": text[:2000],
            }
        finally:
            document.Close(SaveChanges=False)


def create_word_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with WordApp() as session:
        document = session.app.Documents.Add()
        try:
            selection = session.app.Selection
            _write_block(selection, "Merge Header", header_lines)
            for source in sources:
                selection.InsertBreak(WD_PAGE_BREAK)
                _write_block(selection, "Source", _source_lines(source))
                selection.InsertBreak(WD_PAGE_BREAK)
                selection.InsertFile(str(Path(source["absolute_path"]).resolve()))
            document.SaveAs2(str(path.resolve()), FileFormat=WD_FORMAT_XML_DOCUMENT)
        finally:
            document.Close(SaveChanges=False)
    return path


def _write_block(selection: object, title: str, lines: list[str]) -> None:
    selection.Font.Name = "Yu Gothic"
    selection.Font.Bold = True
    selection.Font.Size = 18
    selection.TypeText(title)
    selection.TypeParagraph()
    selection.Font.Bold = False
    selection.Font.Size = 9
    for line in lines:
        for wrapped in _wrap_line(line, size=120):
            selection.TypeText(wrapped)
            selection.TypeParagraph()


def _source_lines(source: dict[str, Any]) -> list[str]:
    return [
        f"Relative path: {source['relative_path']}",
        f"Absolute path: {source['absolute_path']}",
        f"Modified: {source.get('modified_at') or ''}",
        f"Pages: {source.get('page_count') or 0}",
    ]


def _wrap_line(line: str, *, size: int) -> list[str]:
    if len(line) <= size:
        return [line]
    return [line[index : index + size] for index in range(0, len(line), size)]
