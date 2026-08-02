from __future__ import annotations

import json
import traceback
from datetime import UTC, datetime

import pytest

from outlabs_whatsapp import (
    DeliveryStatus,
    InboundInteractiveEvent,
    InboundTextEvent,
    InvalidWebhookSignature,
    MalformedWebhookPayload,
    MessageStatusEvent,
    UnsupportedEvent,
    WebhookVerifier,
    decode_envelope,
    signature_for,
    verify_challenge,
)
from outlabs_whatsapp.testing import (
    build_status_webhook,
    build_text_webhook,
    encode_payload,
    signed_headers,
)


def test_signed_text_webhook_normalizes_without_repr_leakage() -> None:
    raw = build_text_webhook(body="Sensitive synthetic text", from_number="15550001111")
    headers = signed_headers(raw, app_secret="app-secret")
    verifier = WebhookVerifier(app_secret="app-secret", verify_token="verify-token")

    verifier.verify_signature(raw, headers["X-Hub-Signature-256"])
    envelope = decode_envelope(raw, received_at=datetime(2026, 8, 2, tzinfo=UTC))

    assert len(envelope.events) == 1
    event = envelope.events[0]
    assert isinstance(event, InboundTextEvent)
    assert event.body == "Sensitive synthetic text"
    assert event.from_number == "15550001111"
    assert "Sensitive synthetic text" not in repr(event)
    assert "15550001111" not in repr(event)


def test_invalid_signature_rejected() -> None:
    raw = build_text_webhook()
    verifier = WebhookVerifier(app_secret="app-secret", verify_token="verify-token")

    with pytest.raises(InvalidWebhookSignature):
        verifier.verify_signature(raw, "sha256=bad")


def test_status_webhook_normalizes_pricing_and_delivery() -> None:
    raw = build_status_webhook(status="delivered")

    envelope = decode_envelope(raw)

    event = envelope.events[0]
    assert isinstance(event, MessageStatusEvent)
    assert event.status is DeliveryStatus.DELIVERED
    assert event.billable is True
    assert event.pricing_category == "utility"


def test_same_event_has_stable_dedupe_key() -> None:
    raw = build_status_webhook()

    first = decode_envelope(raw).events[0]
    second = decode_envelope(raw).events[0]

    assert first.dedupe_key == second.dedupe_key


def test_unicode_and_unknown_fields_are_tolerated() -> None:
    raw = build_text_webhook(body="Actualización disponible — ingresá al portal ✅")
    payload = json.loads(raw)
    payload["entry"][0]["changes"][0]["value"]["future_meta_field"] = {"ignored": True}

    envelope = decode_envelope(encode_payload(payload))

    event = envelope.events[0]
    assert isinstance(event, InboundTextEvent)
    assert event.body.endswith("✅")


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(MalformedWebhookPayload):
        decode_envelope(b"{not-json")


def test_statuses_preserve_provider_events_without_projecting_state() -> None:
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "test-waba-id",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": "test-phone-number-id"},
                            "statuses": [
                                {
                                    "id": "wamid.same",
                                    "status": "read",
                                    "timestamp": "1785628802",
                                },
                                {
                                    "id": "wamid.same",
                                    "status": "delivered",
                                    "timestamp": "1785628801",
                                },
                            ],
                        },
                    }
                ],
            }
        ],
    }

    envelope = decode_envelope(encode_payload(payload))

    assert [event.status for event in envelope.events if isinstance(event, MessageStatusEvent)] == [
        DeliveryStatus.READ,
        DeliveryStatus.DELIVERED,
    ]


@pytest.mark.parametrize("interactive_type", ["button_reply", "list_reply"])
def test_interactive_replies_normalize(interactive_type: str) -> None:
    payload = json.loads(build_text_webhook())
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    message["type"] = "interactive"
    message.pop("text")
    message["interactive"] = {
        "type": interactive_type,
        interactive_type: {"id": "selection-1", "title": "Private selection"},
    }

    event = decode_envelope(encode_payload(payload)).events[0]

    assert isinstance(event, InboundInteractiveEvent)
    assert event.interactive_type == interactive_type
    assert event.selection_id == "selection-1"
    assert "Private selection" not in repr(event)


def test_legacy_button_reply_normalizes() -> None:
    payload = json.loads(build_text_webhook())
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    message["type"] = "button"
    message.pop("text")
    message["button"] = {"payload": "selection-1", "text": "Private selection"}

    event = decode_envelope(encode_payload(payload)).events[0]

    assert isinstance(event, InboundInteractiveEvent)
    assert event.interactive_type == "button"
    assert "Private selection" not in repr(event)


def test_unknown_status_and_safe_error_codes_are_preserved() -> None:
    payload = json.loads(build_status_webhook(status="future-status"))
    status = payload["entry"][0]["changes"][0]["value"]["statuses"][0]
    status["errors"] = [
        {"code": 131000, "error_subcode": 7, "message": "private provider content"},
        "not-an-error",
    ]

    event = decode_envelope(encode_payload(payload)).events[0]

    assert isinstance(event, MessageStatusEvent)
    assert event.status is DeliveryStatus.UNKNOWN
    assert event.errors[0].code == 131000
    assert event.errors[0].subcode == 7
    assert "private provider content" not in repr(event)


def test_oversized_provider_fields_degrade_to_unsupported_event() -> None:
    payload = json.loads(build_text_webhook())
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    message["id"] = "x" * 513
    message["text"]["body"] = "private" * 10_000

    event = decode_envelope(encode_payload(payload)).events[0]

    assert isinstance(event, UnsupportedEvent)
    assert event.event_type == "message:text"


def test_empty_and_non_object_json_are_rejected() -> None:
    for raw in (b"", b"[]", b'"text"', b'{"value":NaN}', b'{"value":Infinity}'):
        with pytest.raises(MalformedWebhookPayload):
            decode_envelope(raw)


def test_decode_body_cap_and_configuration_are_enforced() -> None:
    with pytest.raises(MalformedWebhookPayload):
        decode_envelope(b"{}", max_body_bytes=1)
    with pytest.raises(ValueError, match="max_body_bytes"):
        decode_envelope(b"{}", max_body_bytes=0)
    for max_events in (0, 10_001):
        with pytest.raises(ValueError, match="max_events"):
            decode_envelope(b"{}", max_events=max_events)
    for max_depth in (0, 257):
        with pytest.raises(ValueError, match="max_json_depth"):
            decode_envelope(b"{}", max_json_depth=max_depth)


def test_received_time_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        decode_envelope(b"{}", received_at=datetime(2026, 8, 2))


def test_signature_header_requires_exact_lowercase_sha256_shape() -> None:
    raw = build_text_webhook()
    verifier = WebhookVerifier(app_secret="app-secret", verify_token="verify-token")

    for invalid in (None, "", "SHA256=" + "0" * 64, "sha256=" + "A" * 64, "sha256=00"):
        with pytest.raises(InvalidWebhookSignature):
            verifier.verify_signature(raw, invalid)


def test_verifier_rejects_empty_or_control_character_secrets() -> None:
    with pytest.raises(ValueError, match="app_secret"):
        WebhookVerifier(app_secret="", verify_token="valid")
    for token in ("", " surrounding ", "line\nbreak"):
        with pytest.raises(ValueError, match="verify_token"):
            WebhookVerifier(app_secret="valid", verify_token=token)

    with pytest.raises(TypeError, match="app_secret"):
        WebhookVerifier(
            app_secret=bytearray(b"mutable"),  # type: ignore[arg-type]
            verify_token="valid",
        )


def test_free_verification_helpers_reject_empty_configuration() -> None:
    with pytest.raises(ValueError, match="app_secret"):
        signature_for(b"payload", b"")
    with pytest.raises(ValueError, match="expected_token"):
        verify_challenge("", "")


def test_verifier_repr_hides_both_secrets() -> None:
    verifier = WebhookVerifier(app_secret="PRIVATE-APP-SECRET", verify_token="PRIVATE-TOKEN")

    rendered = repr(verifier)
    assert "PRIVATE-APP-SECRET" not in rendered
    assert "PRIVATE-TOKEN" not in rendered


def test_envelope_repr_hides_raw_body() -> None:
    raw = build_text_webhook(body="PRIVATE-WEBHOOK-BODY")

    envelope = decode_envelope(raw)

    assert "PRIVATE-WEBHOOK-BODY" not in repr(envelope)


def test_missing_entries_and_invalid_change_shapes_are_tolerated() -> None:
    cases = [
        {"object": "whatsapp_business_account"},
        {"entry": "not-a-list"},
        {"entry": ["not-an-entry", {"id": "waba", "changes": "not-a-list"}]},
        {
            "entry": [
                {
                    "id": "waba",
                    "changes": ["not-a-change", {"field": "messages", "value": "bad"}],
                }
            ]
        },
    ]

    for payload in cases:
        events = decode_envelope(encode_payload(payload)).events
        assert len(events) == 1
        assert isinstance(events[0], UnsupportedEvent)


def test_excess_normalized_events_reject_the_complete_envelope() -> None:
    payload = json.loads(build_text_webhook())
    messages = payload["entry"][0]["changes"][0]["value"]["messages"]
    second = {**messages[0], "id": "wamid.test.inbound.2"}
    messages.append(second)

    with pytest.raises(MalformedWebhookPayload):
        decode_envelope(encode_payload(payload), max_events=1)


def test_deep_json_is_rejected_without_recursion_escape() -> None:
    raw = b'{"nested":' + (b"[" * 2_000) + b"0" + (b"]" * 2_000) + b"}"

    with pytest.raises(MalformedWebhookPayload):
        decode_envelope(raw)


def test_malformed_body_is_suppressed_from_formatted_traceback() -> None:
    sensitive = "PRIVATE-MALFORMED-WEBHOOK-CONTENT"

    with pytest.raises(MalformedWebhookPayload) as captured:
        decode_envelope(f"{{{sensitive}".encode())

    rendered = "".join(traceback.format_exception(captured.value))
    assert sensitive not in rendered
    assert captured.value.__cause__ is None
