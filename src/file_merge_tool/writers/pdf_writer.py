from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from file_merge_tool.domain.recovery import (
    MergeWriteReport,
    RecoveryInfo,
    RecoveryUnit,
    dedupe_steps,
    recovery_overview_lines,
    source_recovery_lines,
    worst_fidelity,
)


def write_pdf_merge(
    path: Path,
    *,
    header_lines: list[str],
    sources: list[dict[str, Any]],
) -> MergeWriteReport:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    recoveries: list[tuple[str, RecoveryInfo]] = []
    source_pages: list[Any] = []

    for source in sources:
        recovery, pages = _build_source_pages(source)
        recoveries.append((str(source["absolute_path"]), recovery))
        source_pages.extend(pages)

    writer.add_page(_text_page("Merge Header", [*header_lines, "", *recovery_overview_lines([info for _, info in recoveries])]))
    for page in source_pages:
        writer.add_page(page)

    with path.open("wb") as file:
        writer.write(file)
    return MergeWriteReport(output_path=path, recoveries=tuple(recoveries))


def _build_source_pages(source: dict[str, Any]) -> tuple[RecoveryInfo, list[Any]]:
    temp_writer = PdfWriter()
    pages: list[Any] = []
    units: list[RecoveryUnit] = []
    reader = source["reader"]
    for page_meta, page in zip(source.get("pages", []), reader.pages):
        page_number = int(page_meta["page_number"])
        for attempt in range(2):
            try:
                temp_writer.add_page(page)
                pages.append(page)
                units.append(
                    RecoveryUnit(
                        unit_type="page",
                        unit_name=f"Page {page_number}",
                        status="merged",
                        fidelity="exact" if attempt == 0 else "retry_recovered",
                        message=None if attempt == 0 else f"Page {page_number} succeeded after retry.",
                        recovery_steps=() if attempt == 0 else ("page_add_retry_recovered",),
                    )
                )
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 1:
                    try:
                        fallback_page = _text_page(
                            f"Recovered Page {page_number}",
                            [
                                f"Source: {source['relative_path']}",
                                f"Original page: {page_number}",
                                f"Recovery note: The original page could not be merged exactly. ({exc})",
                                "",
                                *(
                                    page_meta.get("text_lines", [])
                                    or ["(No readable page text was extracted.)"]
                                ),
                            ],
                        )
                        temp_writer.add_page(fallback_page)
                        pages.append(fallback_page)
                        units.append(
                            RecoveryUnit(
                                unit_type="page",
                                unit_name=f"Page {page_number}",
                                status="merged",
                                fidelity="text_only",
                                message=f"Page {page_number} was rebuilt as a text-only page.",
                                recovery_steps=("page_add_failed", "page_add_retry_failed", "rebuild_text_only"),
                            )
                        )
                    except Exception as rebuild_exc:  # noqa: BLE001
                        units.append(
                            RecoveryUnit(
                                unit_type="page",
                                unit_name=f"Page {page_number}",
                                status="skipped",
                                fidelity="skipped",
                                message=f"Page {page_number} could not be merged or rebuilt: {rebuild_exc}",
                                recovery_steps=("page_add_failed", "page_add_retry_failed", "rebuild_text_only_failed"),
                            )
                        )
                continue

    recovery = _source_recovery_from_units(units)
    divider = _text_page("Source", [*_source_lines(source), "", *source_recovery_lines(recovery)])
    return recovery, [divider, *pages]


def _source_recovery_from_units(units: list[RecoveryUnit]) -> RecoveryInfo:
    merged_units = [unit for unit in units if unit.status == "merged"]
    skipped_units = [unit for unit in units if unit.status == "skipped"]
    if not merged_units:
        return RecoveryInfo(
            status="skipped",
            fidelity="skipped",
            message="The PDF could not be merged after page-level rescue attempts.",
            recovery_steps=("page_level_rescue", "source_skipped"),
            units=tuple(units),
        )

    fidelity = worst_fidelity(unit.fidelity for unit in merged_units)
    messages: list[str] = []
    if fidelity == "text_only":
        messages.append("One or more pages were rebuilt as text-only pages.")
    elif fidelity == "retry_recovered":
        messages.append("One or more pages succeeded after retry.")
    if skipped_units:
        messages.append(f"{len(skipped_units)} page(s) were skipped after rescue attempts.")
    return RecoveryInfo(
        status="merged",
        fidelity=fidelity,
        message=" ".join(dict.fromkeys(message for message in messages if message)) or None,
        recovery_steps=dedupe_steps(step for unit in units for step in unit.recovery_steps),
        units=tuple(units),
    )


def _source_lines(source: dict[str, Any]) -> list[str]:
    return [
        f"Relative path: {source['relative_path']}",
        f"Absolute path: {source['absolute_path']}",
        f"Modified: {source.get('modified_at') or ''}",
        f"Pages: {source.get('page_count') or 0}",
    ]


def _text_page(title: str, lines: list[str]):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_name = _font_name()
    pdf.setFont(font_name, 18)
    pdf.drawString(42, height - 54, title)
    pdf.setFont(font_name, 9)
    y = height - 84
    for line in lines:
        for wrapped in _wrap_line(line, 110):
            if y < 42:
                pdf.showPage()
                pdf.setFont(font_name, 9)
                y = height - 54
            pdf.drawString(42, y, wrapped)
            y -= 14
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def _font_name() -> str:
    font_name = "HeiseiKakuGo-W5"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        return font_name
    except Exception:  # noqa: BLE001
        return "Helvetica"


def _wrap_line(line: str, size: int) -> list[str]:
    if len(line) <= size:
        return [line]
    return [line[index : index + size] for index in range(0, len(line), size)]
