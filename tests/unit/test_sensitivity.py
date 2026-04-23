from file_merge_tool.domain.sensitivity import is_sensitive_text


def test_detects_sensitive_marker_in_subject() -> None:
    assert is_sensitive_text(subject="\u6a5f\u5bc6: plan", body="")


def test_detects_sensitive_marker_in_first_three_non_empty_body_lines() -> None:
    body = "\n\nfirst\nsecond\n\u6975\u79d8 third\nfourth"

    assert is_sensitive_text(subject="", body=body)


def test_ignores_sensitive_marker_after_first_three_non_empty_body_lines() -> None:
    body = "first\nsecond\nthird\n\u6a5f\u5bc6 fourth"

    assert not is_sensitive_text(subject="", body=body)

