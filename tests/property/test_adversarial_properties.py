from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from outlabs_whatsapp import InvalidWebhookSignature, TextCommand, decode_envelope
from outlabs_whatsapp.testing import encode_payload
from outlabs_whatsapp.webhooks import payload_sha256, signature_for, verify_signature


@given(
    raw_body=st.binary(max_size=4096),
    app_secret=st.binary(min_size=1, max_size=128),
)
def test_signature_round_trip_and_body_mutation_rejection(
    raw_body: bytes, app_secret: bytes
) -> None:
    signature = signature_for(raw_body, app_secret)

    verify_signature(raw_body, signature, app_secret)
    with pytest.raises(InvalidWebhookSignature):
        verify_signature(raw_body + b"\x00", signature, app_secret)


@given(
    suffix=st.text(
        alphabet=st.characters(blacklist_categories=("Cs", "Cc")),
        min_size=1,
        max_size=80,
    ),
    recipient=st.integers(min_value=1_000_000, max_value=9_999_999_999_999_999_999),
)
def test_command_repr_never_contains_recipient_or_body(suffix: str, recipient: int) -> None:
    body = f"PRIVATE-CONTENT<{suffix}>"
    command = TextCommand(to=str(recipient), body=body)

    rendered = repr(command)
    assert body not in rendered
    assert str(recipient) not in rendered


json_scalar = st.none() | st.booleans() | st.integers() | st.text(max_size=128)
json_value = st.recursive(
    json_scalar,
    lambda children: st.lists(children, max_size=8)
    | st.dictionaries(st.text(max_size=32), children, max_size=8),
    max_leaves=40,
)


@settings(max_examples=150, suppress_health_check=(HealthCheck.too_slow,))
@given(payload=st.dictionaries(st.text(max_size=32), json_value, max_size=8))
def test_arbitrary_json_objects_always_normalize_to_a_bounded_envelope(
    payload: dict[str, object],
) -> None:
    raw = encode_payload(payload)

    envelope = decode_envelope(raw, received_at=datetime(2026, 8, 2, tzinfo=UTC))

    assert envelope.events
    assert envelope.raw_payload_sha256 == payload_sha256(raw)
    assert all(event.raw_payload_sha256 == envelope.raw_payload_sha256 for event in envelope.events)
