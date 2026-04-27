from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.infrastructure.office_com.office_app import require_pywin32


PP_LAYOUT_BLANK = 12
PP_SAVE_AS_OPEN_XML_PRESENTATION = 24
MSO_TEXT_ORIENTATION_HORIZONTAL = 1


class PowerPointApp:
    def __enter__(self) -> "PowerPointApp":
        require_pywin32()
        import win32com.client  # type: ignore[import-not-found]

        self.app = win32com.client.DispatchEx("PowerPoint.Application")
        self.app.DisplayAlerts = 0
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        quit_app = getattr(self.app, "Quit", None)
        if callable(quit_app):
            quit_app()


def read_powerpoint_info(path: Path) -> dict[str, Any]:
    with PowerPointApp() as session:
        presentation = session.app.Presentations.Open(
            str(path.resolve()),
            ReadOnly=True,
            Untitled=False,
            WithWindow=False,
        )
        try:
            slide_count = int(presentation.Slides.Count)
            first_slide_text = ""
            slides: list[dict[str, Any]] = []
            if slide_count:
                for slide_index in range(1, slide_count + 1):
                    text_lines = _slide_text_lines(presentation.Slides(slide_index))
                    if slide_index == 1:
                        first_slide_text = "\n".join(text_lines)
                    slides.append(
                        {
                            "slide_number": slide_index,
                            "text_lines": text_lines,
                        }
                    )
            return {
                "slide_count": slide_count,
                "first_slide_text": first_slide_text,
                "slides": slides,
            }
        finally:
            presentation.Close()


def create_powerpoint_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with PowerPointApp() as session:
        target = session.app.Presentations.Add(WithWindow=False)
        try:
            _add_text_slide(
                target,
                title="Merge Header",
                lines=header_lines,
                accent=True,
            )
            for source in sources:
                _add_text_slide(
                    target,
                    title="Source",
                    lines=_source_lines(source),
                    accent=False,
                )
                target.Slides.InsertFromFile(
                    str(Path(source["absolute_path"]).resolve()),
                    target.Slides.Count,
                )
            target.SaveAs(str(path.resolve()), PP_SAVE_AS_OPEN_XML_PRESENTATION)
        finally:
            target.Close()
    return path


def _slide_text_lines(slide: object) -> list[str]:
    texts: list[str] = []
    for shape in slide.Shapes:
        try:
            if shape.HasTextFrame and shape.TextFrame.HasText:
                text = str(shape.TextFrame.TextRange.Text).strip()
                if text:
                    texts.extend(line for line in text.splitlines() if line.strip())
        except Exception:  # noqa: BLE001
            continue
    return texts


def _source_lines(source: dict[str, Any]) -> list[str]:
    return [
        f"Relative path: {source['relative_path']}",
        f"Absolute path: {source['absolute_path']}",
        f"Modified: {source.get('modified_at') or ''}",
        f"Slides: {source.get('slide_count') or 0}",
    ]


def _add_text_slide(
    presentation: object,
    *,
    title: str,
    lines: list[str],
    accent: bool,
) -> None:
    slide = presentation.Slides.Add(presentation.Slides.Count + 1, PP_LAYOUT_BLANK)
    background = slide.Background.Fill
    background.Solid()
    background.ForeColor.RGB = _rgb(251, 248, 241)

    _add_textbox(
        slide,
        title,
        left=42,
        top=34,
        width=840,
        height=32,
        font_size=22 if accent else 18,
        color=_rgb(38, 34, 29),
        bold=True,
    )
    _add_rule(slide)
    _add_textbox(
        slide,
        "\n".join(_wrap_lines(lines, size=110)),
        left=42,
        top=86,
        width=850,
        height=430,
        font_size=8,
        color=_rgb(56, 51, 43),
        bold=False,
    )


def _add_textbox(
    slide: object,
    text: str,
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    font_size: int,
    color: int,
    bold: bool,
) -> None:
    shape = slide.Shapes.AddTextbox(
        MSO_TEXT_ORIENTATION_HORIZONTAL,
        left,
        top,
        width,
        height,
    )
    text_range = shape.TextFrame.TextRange
    text_range.Text = text
    text_range.Font.Name = "Yu Gothic"
    text_range.Font.Size = font_size
    text_range.Font.Bold = -1 if bold else 0
    text_range.Font.Color.RGB = color


def _add_rule(slide: object) -> None:
    shape = slide.Shapes.AddShape(1, 42, 74, 850, 2)
    shape.Fill.ForeColor.RGB = _rgb(143, 111, 62)
    shape.Line.ForeColor.RGB = _rgb(143, 111, 62)


def _wrap_lines(lines: list[str], *, size: int) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        if len(line) <= size:
            wrapped.append(line)
            continue
        wrapped.extend(line[index : index + size] for index in range(0, len(line), size))
    return wrapped


def _rgb(red: int, green: int, blue: int) -> int:
    return red + (green * 256) + (blue * 65536)
