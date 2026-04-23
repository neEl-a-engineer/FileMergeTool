from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MSG_EXTENSIONS = frozenset({".msg"})


@dataclass(frozen=True)
class ExtractedMessage:
    subject: str
    received_at: str
    sender: str
    recipients: list[str]
    body_lines: list[str]
    attachment_names: list[str]


def is_msg_file(path: Path) -> bool:
    return path.suffix.lower() in MSG_EXTENSIONS


def extract_msg_file(path: Path) -> ExtractedMessage:
    try:
        import extract_msg  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "extract-msg is required to merge .msg files. Install the office dependencies."
        ) from exc

    message = extract_msg.Message(str(path))
    try:
        subject = _string_value(getattr(message, "subject", ""))
        received_at = _string_value(
            getattr(message, "date", "")
            or getattr(message, "headerDate", "")
            or getattr(message, "receivedTime", "")
        )
        sender = _string_value(
            getattr(message, "sender", "")
            or getattr(message, "senderEmail", "")
            or getattr(message, "from_", "")
        )
        recipients = _recipients(message)
        body = _string_value(getattr(message, "body", "") or getattr(message, "htmlBody", ""))
        return ExtractedMessage(
            subject=subject,
            received_at=received_at,
            sender=sender,
            recipients=recipients,
            body_lines=body.splitlines(),
            attachment_names=_attachment_names(message),
        )
    finally:
        close = getattr(message, "close", None)
        if callable(close):
            close()


def _recipients(message: object) -> list[str]:
    values = [
        getattr(message, "to", ""),
        getattr(message, "cc", ""),
        getattr(message, "bcc", ""),
    ]
    recipients: list[str] = []
    for value in values:
        text = _string_value(value)
        if not text:
            continue
        for part in text.replace("\n", ";").split(";"):
            item = part.strip()
            if item:
                recipients.append(item)
    return recipients


def _attachment_names(message: object) -> list[str]:
    names: list[str] = []
    for attachment in getattr(message, "attachments", []) or []:
        name = (
            getattr(attachment, "longFilename", None)
            or getattr(attachment, "shortFilename", None)
            or getattr(attachment, "filename", None)
        )
        text = _string_value(name)
        if text:
            names.append(text)
    return names


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
