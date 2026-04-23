from __future__ import annotations

from file_merge_tool.application.create_file_list import create_file_list
from file_merge_tool.application.merge_excel import merge_excel
from file_merge_tool.application.merge_image import merge_image
from file_merge_tool.application.merge_mail import merge_mail
from file_merge_tool.application.merge_pdf import merge_pdf
from file_merge_tool.application.merge_powerpoint import merge_powerpoint
from file_merge_tool.application.merge_text import merge_text
from file_merge_tool.application.merge_word import merge_word
from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.merge_job import MergeKind
from file_merge_tool.domain.result import MergeResult


def run_job(kind: MergeKind, request: MergeRequest) -> MergeResult:
    if kind == MergeKind.FILE_LIST:
        return create_file_list(request)
    if kind == MergeKind.TEXT_MERGE:
        return merge_text(request)
    if kind == MergeKind.MAIL_MERGE:
        return merge_mail(request)
    if kind == MergeKind.POWERPOINT_MERGE:
        return merge_powerpoint(request)
    if kind == MergeKind.EXCEL_MERGE:
        return merge_excel(request)
    if kind == MergeKind.WORD_MERGE:
        return merge_word(request)
    if kind == MergeKind.PDF_MERGE:
        return merge_pdf(request)
    if kind == MergeKind.IMAGE_MERGE:
        return merge_image(request)
    raise ValueError(f"Unsupported merge kind: {kind}")
