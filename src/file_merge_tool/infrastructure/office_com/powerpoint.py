from __future__ import annotations

from pathlib import Path
from typing import Any

from file_merge_tool.domain.recovery import (
    MergeWriteReport,
    RecoveryInfo,
    RecoveryUnit,
    dedupe_steps,
    recovery_overview_lines,
    source_recovery_lines,
    worst_fidelity,
)
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
) -> MergeWriteReport:
    path.parent.mkdir(parents=True, exist_ok=True)
    recoveries: list[tuple[str, RecoveryInfo]] = []
    with PowerPointApp() as session:
        target = session.app.Presentations.Add(WithWindow=False)
        try:
            header_slide = _add_text_slide(
                target,
                title="Merge Header",
                lines=header_lines,
                accent=True,
            )
            for source in sources:
                divider_slide = _add_text_slide(
                    target,
                    title="Source",
                    lines=_source_lines(source),
                    accent=False,
                )
                recovery = _merge_source_presentation(target=target, source=source)
                recoveries.append((str(source["absolute_path"]), recovery))
                _render_text_slide(
                    divider_slide,
                    title="Source",
                    lines=[*_source_lines(source), "", *source_recovery_lines(recovery)],
                    accent=False,
                )
            _render_text_slide(
                header_slide,
                title="Merge Header",
                lines=[*header_lines, "", *recovery_overview_lines([info for _, info in recoveries])],
                accent=True,
            )
            target.SaveAs(str(path.resolve()), PP_SAVE_AS_OPEN_XML_PRESENTATION)
        finally:
            target.Close()
    return MergeWriteReport(output_path=path, recoveries=tuple(recoveries))


def _merge_source_presentation(*, target: object, source: dict[str, Any]) -> RecoveryInfo:
    source_path = str(Path(source["absolute_path"]).resolve())
    full_insert_retried = False
    for attempt in range(2):
        try:
            target.Slides.InsertFromFile(source_path, target.Slides.Count)
            if attempt == 0:
                return RecoveryInfo(status="merged", fidelity="exact")
            return RecoveryInfo(
                status="merged",
                fidelity="retry_recovered",
                message="The presentation succeeded after retry.",
                recovery_steps=("presentation_insert_retry_recovered",),
            )
        except Exception:  # noqa: BLE001
            full_insert_retried = full_insert_retried or attempt == 0
            continue

    units: list[RecoveryUnit] = []
    for slide in source.get("slides", []):
        slide_number = int(slide["slide_number"])
        inserted = False
        retried = False
        for attempt in range(2):
            try:
                target.Slides.InsertFromFile(source_path, target.Slides.Count, slide_number, slide_number)
                units.append(
                    RecoveryUnit(
                        unit_type="slide",
                        unit_name=f"Slide {slide_number}",
                        status="merged",
                        fidelity="exact" if attempt == 0 else "retry_recovered",
                        message=None if attempt == 0 else f"Slide {slide_number} succeeded after retry.",
                        recovery_steps=() if attempt == 0 else ("slide_insert_retry_recovered",),
                    )
                )
                inserted = True
                break
            except Exception:  # noqa: BLE001
                retried = retried or attempt == 0
                continue
        if inserted:
            continue

        try:
            _add_recovered_slide(target, source=source, slide=slide)
            units.append(
                RecoveryUnit(
                    unit_type="slide",
                    unit_name=f"Slide {slide_number}",
                    status="merged",
                    fidelity="text_only",
                    message=f"Slide {slide_number} was rebuilt as a text-only slide.",
                    recovery_steps=(
                        "slide_insert_failed",
                        "slide_insert_retry_failed" if retried else "slide_insert_failed",
                        "rebuild_text_only",
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            units.append(
                RecoveryUnit(
                    unit_type="slide",
                    unit_name=f"Slide {slide_number}",
                    status="skipped",
                    fidelity="skipped",
                    message=f"Slide {slide_number} could not be inserted or rebuilt: {exc}",
                    recovery_steps=(
                        "slide_insert_failed",
                        "slide_insert_retry_failed" if retried else "slide_insert_failed",
                        "rebuild_text_only_failed",
                    ),
                )
            )

    return _source_recovery_from_units(
        units,
        base_steps=("presentation_insert_failed", "slide_level_rescue"),
        full_insert_retried=full_insert_retried,
    )


def _source_recovery_from_units(
    units: list[RecoveryUnit],
    *,
    base_steps: tuple[str, ...],
    full_insert_retried: bool,
) -> RecoveryInfo:
    merged_units = [unit for unit in units if unit.status == "merged"]
    skipped_units = [unit for unit in units if unit.status == "skipped"]
    if not merged_units:
        return RecoveryInfo(
            status="skipped",
            fidelity="skipped",
            message="The presentation could not be merged after slide-level rescue attempts.",
            recovery_steps=dedupe_steps((*base_steps, "source_skipped")),
            units=tuple(units),
        )

    fidelity = worst_fidelity(unit.fidelity for unit in merged_units)
    messages: list[str] = []
    if fidelity == "text_only":
        messages.append("One or more slides were rebuilt as text-only slides.")
    elif fidelity == "retry_recovered" or full_insert_retried:
        messages.append("One or more slides succeeded after retry.")
    if skipped_units:
        messages.append(f"{len(skipped_units)} slide(s) were skipped after rescue attempts.")
    return RecoveryInfo(
        status="merged",
        fidelity=fidelity,
        message=" ".join(dict.fromkeys(message for message in messages if message)) or None,
        recovery_steps=dedupe_steps((*base_steps, *(step for unit in units for step in unit.recovery_steps))),
        units=tuple(units),
    )


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
) -> object:
    slide = presentation.Slides.Add(presentation.Slides.Count + 1, PP_LAYOUT_BLANK)
    _render_text_slide(slide, title=title, lines=lines, accent=accent)
    return slide


def _render_text_slide(
    slide: object,
    *,
    title: str,
    lines: list[str],
    accent: bool,
) -> None:
    _clear_slide(slide)
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


def _add_recovered_slide(target: object, *, source: dict[str, Any], slide: dict[str, Any]) -> None:
    slide_number = int(slide["slide_number"])
    text_lines = [line for line in slide.get("text_lines", []) if str(line).strip()]
    lines = [
        f"Source: {source['relative_path']}",
        f"Original slide: {slide_number}",
        "Recovery note: The original slide could not be inserted. Text content was preserved below.",
        "",
        *(text_lines or ["(No readable slide text was extracted.)"]),
    ]
    recovered_slide = _add_text_slide(
        target,
        title=f"Recovered Slide {slide_number}",
        lines=lines,
        accent=False,
    )
    _add_placeholder_box(recovered_slide)


def _clear_slide(slide: object) -> None:
    for index in range(int(slide.Shapes.Count), 0, -1):
        slide.Shapes(index).Delete()


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


def _add_placeholder_box(slide: object) -> None:
    box = slide.Shapes.AddShape(1, 42, 360, 850, 120)
    box.Fill.ForeColor.RGB = _rgb(245, 238, 224)
    box.Line.ForeColor.RGB = _rgb(143, 111, 62)
    text_range = box.TextFrame.TextRange
    text_range.Text = "Visual content placeholder\nThe original slide shapes could not be recreated in-place."
    text_range.Font.Name = "Yu Gothic"
    text_range.Font.Size = 10
    text_range.Font.Color.RGB = _rgb(56, 51, 43)


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
