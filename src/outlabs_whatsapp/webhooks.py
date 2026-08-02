"""Provider-independent webhook envelope and Meta verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from outlabs_whatsapp.errors import (
    InvalidWebhookChallenge,
    InvalidWebhookSignature,
    MalformedWebhookPayload,
)
from outlabs_whatsapp.events import NormalizedEvent
from outlabs_whatsapp.meta.normalize import normalize_payload


class WebhookAcceptance(StrEnum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"


class WebhookEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    events: tuple[NormalizedEvent, ...]
    raw_body: bytes = Field(repr=False)
    raw_payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    received_at: AwareDatetime


class EventSink(Protocol):
    async def accept(self, envelope: WebhookEnvelope) -> WebhookAcceptance: ...


def payload_sha256(raw_body: bytes) -> str:
    return hashlib.sha256(raw_body).hexdigest()


def signature_for(raw_body: bytes, app_secret: str | bytes) -> str:
    secret = app_secret.encode("utf-8") if isinstance(app_secret, str) else app_secret
    digest = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(
    raw_body: bytes,
    signature_header: str | None,
    app_secret: str | bytes,
) -> None:
    if not signature_header or re.fullmatch(r"sha256=[a-f0-9]{64}", signature_header) is None:
        raise InvalidWebhookSignature()
    expected = signature_for(raw_body, app_secret)
    if not hmac.compare_digest(signature_header, expected):
        raise InvalidWebhookSignature()


def verify_challenge(received_token: str | None, expected_token: str) -> None:
    if received_token is None or not hmac.compare_digest(received_token, expected_token):
        raise InvalidWebhookChallenge()


class WebhookVerifier:
    """Holds endpoint-scoped webhook secrets without exposing them in repr."""

    __slots__ = ("_app_secret", "_verify_token")

    def __init__(self, *, app_secret: str | bytes, verify_token: str) -> None:
        secret = app_secret.encode("utf-8") if isinstance(app_secret, str) else app_secret
        if not secret:
            raise ValueError("app_secret must not be empty")
        if not verify_token or verify_token != verify_token.strip() or any(
            ord(character) < 32 or ord(character) == 127 for character in verify_token
        ):
            raise ValueError(
                "verify_token must not be empty or contain surrounding/control whitespace"
            )
        self._app_secret = secret
        self._verify_token = verify_token

    def __repr__(self) -> str:
        return "WebhookVerifier(app_secret=***, verify_token=***)"

    def verify_signature(self, raw_body: bytes, signature_header: str | None) -> None:
        verify_signature(raw_body, signature_header, self._app_secret)

    def verify_challenge(self, received_token: str | None) -> None:
        verify_challenge(received_token, self._verify_token)


def decode_envelope(
    raw_body: bytes,
    *,
    received_at: datetime | None = None,
    max_body_bytes: int = 16_000_000,
) -> WebhookEnvelope:
    if not 1 <= max_body_bytes <= 16_000_000:
        raise ValueError("max_body_bytes must be between 1 and 16000000")
    if not raw_body or len(raw_body) > max_body_bytes:
        raise MalformedWebhookPayload()
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise MalformedWebhookPayload() from exc
    if not isinstance(payload, dict):
        raise MalformedWebhookPayload()
    received = received_at or datetime.now(UTC)
    if received.tzinfo is None or received.utcoffset() is None:
        raise ValueError("received_at must be timezone-aware")
    digest = payload_sha256(raw_body)
    events: Sequence[NormalizedEvent] = normalize_payload(
        payload,
        raw_payload_sha256=digest,
        received_at=received,
    )
    return WebhookEnvelope(
        events=tuple(events),
        raw_body=raw_body,
        raw_payload_sha256=digest,
        received_at=received,
    )


__all__ = [
    "EventSink",
    "WebhookAcceptance",
    "WebhookEnvelope",
    "WebhookVerifier",
    "decode_envelope",
    "payload_sha256",
    "signature_for",
    "verify_challenge",
    "verify_signature",
]
