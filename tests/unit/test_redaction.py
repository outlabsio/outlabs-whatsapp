from __future__ import annotations

import pytest

from outlabs_whatsapp.redaction import fingerprint, masked_suffix


def test_fingerprint_is_stable_and_does_not_expose_input() -> None:
    first = fingerprint("private-value")
    second = fingerprint(b"private-value")

    assert first == second
    assert len(first) == 12
    assert "private-value" not in first


@pytest.mark.parametrize("length", [0, 7, 65])
def test_fingerprint_rejects_unsafe_lengths(length: int) -> None:
    with pytest.raises(ValueError, match="between 8 and 64"):
        fingerprint("value", length=length)


def test_masked_suffix_never_reveals_an_entire_short_value() -> None:
    assert masked_suffix("1234") == "***"
    assert masked_suffix("12345") == "***2345"
    assert masked_suffix("12345", visible=0) == "***"


def test_masked_suffix_rejects_negative_visibility() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        masked_suffix("value", visible=-1)
