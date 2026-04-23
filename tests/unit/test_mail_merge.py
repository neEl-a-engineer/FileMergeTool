from __future__ import annotations

import json
from pathlib import Path

from file_merge_tool.application import merge_mail as merge_mail_module
from file_merge_tool.application.merge_mail import merge_mail
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.extractors.msg_extractor import ExtractedMessage


def test_mail_merge_writes_normal_and_sensitive_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "normal.msg").write_bytes(b"placeholder")
    (root / "sensitive.msg").write_bytes(b"placeholder")

    def fake_extract(path: Path) -> ExtractedMessage:
        if path.name == "sensitive.msg":
            return ExtractedMessage(
                subject="Quarterly note",
                received_at="2026-04-23T10:00:00+09:00",
                sender="sender@example.com",
                recipients=["owner@example.com"],
                body_lines=["", "hello", "\u6975\u79d8 project", "details"],
                attachment_names=["plan.xlsx"],
            )
        return ExtractedMessage(
            subject="Open memo",
            received_at="2026-04-23T09:00:00+09:00",
            sender="sender@example.com",
            recipients=["reader@example.com"],
            body_lines=["line 1", "line 2"],
            attachment_names=[],
        )

    monkeypatch.setattr(merge_mail_module, "extract_msg_file", fake_extract)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="mail.json",
        output_stem="mail",
        exclude=ExcludeConfig(),
        kind="mail-merge",
    )

    result = merge_mail(request)

    assert result.item_count == 2
    assert [path.name for path in result.output_paths] == [
        "mail.json",
        "mail_\u6a5f\u5bc6.json",
    ]
    normal = json.loads(result.output_paths[0].read_text(encoding="utf-8"))
    sensitive = json.loads(result.output_paths[1].read_text(encoding="utf-8"))
    assert normal["items"][0]["subject"] == "Open memo"
    assert sensitive["items"][0]["attachment_names"] == ["plan.xlsx"]
    assert sensitive["items"][0]["sensitivity"]["matched_markers"] == ["\u6975\u79d8"]


def test_mail_merge_classifies_only_subject_or_first_three_non_empty_body_lines(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "late-marker.msg").write_bytes(b"placeholder")

    def fake_extract(_: Path) -> ExtractedMessage:
        return ExtractedMessage(
            subject="Open memo",
            received_at="",
            sender="",
            recipients=[],
            body_lines=["one", "", "two", "three", "\u6a5f\u5bc6 too late"],
            attachment_names=[],
        )

    monkeypatch.setattr(merge_mail_module, "extract_msg_file", fake_extract)

    request = MergeRequest(
        root_path=root,
        output_dir=tmp_path / "out",
        output_name="mail.json",
        output_stem="mail",
        exclude=ExcludeConfig(),
        kind="mail-merge",
    )

    result = merge_mail(request)
    normal = json.loads(result.output_paths[0].read_text(encoding="utf-8"))
    sensitive = json.loads(result.output_paths[1].read_text(encoding="utf-8"))

    assert result.item_count == 1
    assert len(normal["items"]) == 1
    assert sensitive["items"] == []
