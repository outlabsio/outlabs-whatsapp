"""Sanitized Meta webhook builders for consumer tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from outlabs_whatsapp.webhooks import signature_for


def encode_payload(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def signed_headers(raw_body: bytes, *, app_secret: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature_for(raw_body, app_secret),
    }


def build_text_webhook(
    *,
    body: str = "Synthetic test message",
    from_number: str = "15550001111",
    message_id: str = "wamid.test.inbound.1",
    timestamp: str = "1785628800",
    waba_id: str = "test-waba-id",
    phone_number_id: str = "test-phone-number-id",
) -> bytes:
    return encode_payload(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": waba_id,
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": phone_number_id},
                                "messages": [
                                    {
                                        "from": from_number,
                                        "id": message_id,
                                        "timestamp": timestamp,
                                        "type": "text",
                                        "text": {"body": body},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    )


def build_status_webhook(
    *,
    status: str = "delivered",
    recipient_id: str = "15550001111",
    message_id: str = "wamid.test.outbound.1",
    timestamp: str = "1785628800",
    waba_id: str = "test-waba-id",
    phone_number_id: str = "test-phone-number-id",
) -> bytes:
    return encode_payload(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": waba_id,
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": phone_number_id},
                                "statuses": [
                                    {
                                        "id": message_id,
                                        "status": status,
                                        "timestamp": timestamp,
                                        "recipient_id": recipient_id,
                                        "pricing": {
                                            "billable": True,
                                            "category": "utility",
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    )


__all__ = [
    "build_status_webhook",
    "build_text_webhook",
    "encode_payload",
    "signed_headers",
]
