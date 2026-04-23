from __future__ import annotations


def require_pywin32() -> None:
    try:
        import win32com.client  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install the optional office dependencies to use Office merge.") from exc

