"""Functional smoke executed with isolated Python against an installed wheel."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from fastapi import FastAPI

import outlabs_whatsapp
from outlabs_whatsapp import MetaCloudClient, TextCommand, WebhookVerifier, decode_envelope
from outlabs_whatsapp.fastapi import create_meta_webhook_router
from outlabs_whatsapp.testing import FakeEventSink, build_text_webhook, signed_headers


async def main() -> None:
    package_path = Path(outlabs_whatsapp.__file__).resolve()
    assert "site-packages" in package_path.parts

    raw = build_text_webhook(body="Synthetic installed-wheel message")
    headers = signed_headers(raw, app_secret="synthetic-app-secret")
    verifier = WebhookVerifier(
        app_secret="synthetic-app-secret",
        verify_token="synthetic-verify-token",
    )
    verifier.verify_signature(raw, headers["X-Hub-Signature-256"])
    envelope = decode_envelope(raw)
    assert len(envelope.events) == 1

    sink = FakeEventSink()
    app = FastAPI()
    app.include_router(create_meta_webhook_router(verifier=verifier, event_sink=sink))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://installed-wheel.test",
    ) as webhook_client:
        response = await webhook_client.post(
            "/integrations/whatsapp/meta",
            content=raw,
            headers=headers,
        )
    assert response.status_code == 200
    assert len(sink.envelopes) == 1

    async def meta_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer synthetic-access-token"
        return httpx.Response(200, json={"messages": [{"id": "wamid.installed-wheel"}]})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(meta_handler),
        base_url="https://graph.facebook.com",
    ) as http_client:
        provider = MetaCloudClient(
            access_token="synthetic-access-token",
            phone_number_id="synthetic-phone-id",
            graph_version="v99.0",
            http_client=http_client,
        )
        result = await provider.send(
            TextCommand(to="15550001111", body="Synthetic installed-wheel outbound")
        )
    assert result.message_id == "wamid.installed-wheel"


if __name__ == "__main__":
    asyncio.run(main())
