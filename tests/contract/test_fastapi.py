from __future__ import annotations

import asyncio
import json
import traceback
from typing import cast

import httpx
import pytest
from fastapi import FastAPI

from outlabs_whatsapp.fastapi import create_meta_webhook_router
from outlabs_whatsapp.testing import (
    FakeEventSink,
    build_text_webhook,
    encode_payload,
    signed_headers,
)
from outlabs_whatsapp.webhooks import EventSink, WebhookAcceptance, WebhookEnvelope, WebhookVerifier


def _app(
    sink: EventSink,
    *,
    max_body_bytes: int = 1_000_000,
    max_events: int = 1_000,
    max_json_depth: int = 64,
) -> FastAPI:
    app = FastAPI()
    app.include_router(
        create_meta_webhook_router(
            verifier=WebhookVerifier(app_secret="app-secret", verify_token="verify-token"),
            event_sink=sink,
            max_body_bytes=max_body_bytes,
            max_events=max_events,
            max_json_depth=max_json_depth,
        )
    )
    return app


@pytest.mark.asyncio
async def test_challenge_requires_exact_token() -> None:
    sink = FakeEventSink()
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        accepted = await client.get(
            "/integrations/whatsapp/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify-token",
                "hub.challenge": "challenge-value",
            },
        )
        rejected = await client.get(
            "/integrations/whatsapp/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong",
                "hub.challenge": "challenge-value",
            },
        )

    assert accepted.status_code == 200
    assert accepted.text == "challenge-value"
    assert rejected.status_code == 403


@pytest.mark.asyncio
async def test_post_verifies_before_sink_and_accepts_signed_event() -> None:
    sink = FakeEventSink()
    raw = build_text_webhook()
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        rejected = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=bad"},
        )
        accepted = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=signed_headers(raw, app_secret="app-secret"),
        )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert len(sink.envelopes) == 1


@pytest.mark.asyncio
async def test_oversized_body_is_rejected_before_sink() -> None:
    sink = FakeEventSink()
    raw = b"x" * 1025
    transport = httpx.ASGITransport(app=_app(sink, max_body_bytes=1024))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=signed_headers(raw, app_secret="app-secret"),
        )

    assert response.status_code == 413
    assert sink.envelopes == []


def test_router_rejects_unsafe_configuration() -> None:
    sink = FakeEventSink()
    verifier = WebhookVerifier(app_secret="app-secret", verify_token="verify-token")

    with pytest.raises(ValueError, match="path"):
        create_meta_webhook_router(path="relative", verifier=verifier, event_sink=sink)
    for body_cap in (1023, 16_000_001):
        with pytest.raises(ValueError, match="max_body_bytes"):
            create_meta_webhook_router(
                verifier=verifier,
                event_sink=sink,
                max_body_bytes=body_cap,
            )
    for event_cap in (0, 10_001):
        with pytest.raises(ValueError, match="max_events"):
            create_meta_webhook_router(
                verifier=verifier,
                event_sink=sink,
                max_events=event_cap,
            )
    for depth_cap in (0, 257):
        with pytest.raises(ValueError, match="max_json_depth"):
            create_meta_webhook_router(
                verifier=verifier,
                event_sink=sink,
                max_json_depth=depth_cap,
            )


@pytest.mark.asyncio
async def test_challenge_rejects_missing_mode_or_challenge() -> None:
    sink = FakeEventSink()
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        missing_mode = await client.get(
            "/integrations/whatsapp/meta",
            params={"hub.verify_token": "verify-token", "hub.challenge": "challenge"},
        )
        missing_challenge = await client.get(
            "/integrations/whatsapp/meta",
            params={"hub.mode": "subscribe", "hub.verify_token": "verify-token"},
        )
        oversized_challenge = await client.get(
            "/integrations/whatsapp/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify-token",
                "hub.challenge": "x" * 1_025,
            },
        )
        control_challenge = await client.get(
            "/integrations/whatsapp/meta",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify-token",
                "hub.challenge": "line\nbreak",
            },
        )

    assert missing_mode.status_code == 403
    assert missing_challenge.status_code == 403
    assert oversized_challenge.status_code == 403
    assert control_challenge.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Type": "text/plain"},
        {"Content-Type": "application/json", "Content-Encoding": "gzip"},
        {},
    ],
)
async def test_post_rejects_unsupported_media_before_sink(headers: dict[str, str]) -> None:
    sink = FakeEventSink()
    raw = build_text_webhook()
    signature = signed_headers(raw, app_secret="app-secret")["X-Hub-Signature-256"]
    request_headers = {**headers, "X-Hub-Signature-256": signature}
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta", content=raw, headers=request_headers
        )

    assert response.status_code == 415
    assert sink.envelopes == []


@pytest.mark.asyncio
async def test_invalid_content_length_is_rejected_before_sink() -> None:
    sink = FakeEventSink()
    raw = build_text_webhook()
    headers = signed_headers(raw, app_secret="app-secret")
    headers["Content-Length"] = "not-a-number"
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta", content=raw, headers=headers
        )

    assert response.status_code == 413
    assert sink.envelopes == []


@pytest.mark.asyncio
async def test_invalid_signature_wins_over_malformed_json() -> None:
    sink = FakeEventSink()
    raw = b"{private malformed body"
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        invalid_signature = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=bad"},
        )
        signed_malformed = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=signed_headers(raw, app_secret="app-secret"),
        )

    assert invalid_signature.status_code == 401
    assert signed_malformed.status_code == 400
    assert "private malformed body" not in invalid_signature.text
    assert "private malformed body" not in signed_malformed.text


@pytest.mark.asyncio
async def test_duplicate_acceptance_returns_success() -> None:
    sink = FakeEventSink(acceptance=WebhookAcceptance.DUPLICATE)
    raw = build_text_webhook()
    transport = httpx.ASGITransport(app=_app(sink))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=signed_headers(raw, app_secret="app-secret"),
        )

    assert response.status_code == 200
    assert len(sink.envelopes) == 1


@pytest.mark.asyncio
async def test_invalid_sink_acceptance_fails_closed() -> None:
    sink = FakeEventSink()
    sink.acceptance = cast(WebhookAcceptance, "unexpected")
    raw = build_text_webhook()
    transport = httpx.ASGITransport(app=_app(sink), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=signed_headers(raw, app_secret="app-secret"),
        )

    assert response.status_code == 500
    assert "Synthetic test message" not in response.text


@pytest.mark.asyncio
async def test_streamed_body_cap_is_enforced_without_content_length() -> None:
    async def chunks():
        yield b"x" * 600
        yield b"y" * 600

    sink = FakeEventSink()
    transport = httpx.ASGITransport(app=_app(sink, max_body_bytes=1024))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta",
            content=chunks(),
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=" + "0" * 64,
            },
        )

    assert response.status_code == 413
    assert sink.envelopes == []


@pytest.mark.asyncio
async def test_normalized_event_cap_rejects_entire_signed_envelope() -> None:
    sink = FakeEventSink()
    payload = json.loads(build_text_webhook())
    messages = payload["entry"][0]["changes"][0]["value"]["messages"]
    messages.append({**messages[0], "id": "wamid.test.inbound.2"})
    raw = encode_payload(payload)
    transport = httpx.ASGITransport(app=_app(sink, max_events=1))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=signed_headers(raw, app_secret="app-secret"),
        )

    assert response.status_code == 400
    assert sink.envelopes == []


@pytest.mark.asyncio
async def test_sink_exception_text_is_suppressed_and_cancellation_propagates() -> None:
    sensitive = "PRIVATE-SINK-FAILURE-CONTENT"

    class FailingSink:
        async def accept(self, envelope: WebhookEnvelope) -> WebhookAcceptance:
            raise RuntimeError(sensitive)

    raw = build_text_webhook()
    transport = httpx.ASGITransport(app=_app(FailingSink()))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with pytest.raises(RuntimeError, match="event sink failed") as captured:
            await client.post(
                "/integrations/whatsapp/meta",
                content=raw,
                headers=signed_headers(raw, app_secret="app-secret"),
            )

    rendered = "".join(traceback.format_exception(captured.value))
    assert sensitive not in rendered
    assert captured.value.__cause__ is None

    class CancelledSink:
        async def accept(self, envelope: WebhookEnvelope) -> WebhookAcceptance:
            raise asyncio.CancelledError

    transport = httpx.ASGITransport(app=_app(CancelledSink()))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with pytest.raises(asyncio.CancelledError):
            await client.post(
                "/integrations/whatsapp/meta",
                content=raw,
                headers=signed_headers(raw, app_secret="app-secret"),
            )
