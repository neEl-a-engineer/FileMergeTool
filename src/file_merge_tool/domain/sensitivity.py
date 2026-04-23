from __future__ import annotations


SENSITIVE_MARKERS = ("\u6a5f\u5bc6", "\u6975\u79d8")


def contains_sensitive_marker(text: str) -> bool:
    return any(marker in text for marker in SENSITIVE_MARKERS)


def first_non_empty_lines(text: str, limit: int = 3) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lines.append(stripped)
        if len(lines) >= limit:
            break
    return lines


def is_sensitive_text(subject: str = "", body: str = "") -> bool:
    header_text = "\n".join(first_non_empty_lines(body, limit=3))
    return contains_sensitive_marker(subject) or contains_sensitive_marker(header_text)

