"""Small helpers for safe operational identifiers."""

from __future__ import annotations

import hashlib


def fingerprint(value: str | bytes, *, length: int = 12) -> str:
    """Return a stable, non-reversible diagnostic fingerprint."""

    if not 8 <= length <= 64:
        raise ValueError("fingerprint length must be between 8 and 64")
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()[:length]


def masked_suffix(value: str, *, visible: int = 4) -> str:
    """Mask an identifier while retaining a small diagnostic suffix."""

    if visible < 0:
        raise ValueError("visible must be non-negative")
    suffix = value[-visible:] if visible and len(value) > visible else ""
    return f"***{suffix}"


__all__ = ["fingerprint", "masked_suffix"]
