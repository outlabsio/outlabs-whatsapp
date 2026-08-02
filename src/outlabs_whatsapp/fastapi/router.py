"""Optional signature-first FastAPI webhook adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse

from outlabs_whatsapp.errors import (
    InvalidWebhookChallenge,
    InvalidWebhookSignature,
    MalformedWebhookPayload,
)
from outlabs_whatsapp.webhooks import (
    EventSink,
    WebhookAcceptance,
    WebhookVerifier,
    decode_envelope,
)


def create_meta_webhook_router(
    *,
    path: str = "/integrations/whatsapp/meta",
    verifier: WebhookVerifier,
    event_sink: EventSink,
    max_body_bytes: int = 1_000_000,
) -> APIRouter:
    if not path.startswith("/"):
        raise ValueError("path must start with /")
    if not 1024 <= max_body_bytes <= 16_000_000:
        raise ValueError("max_body_bytes must be between 1024 and 16000000")

    router = APIRouter(tags=["whatsapp-webhook"])

    async def verify_endpoint(request: Request) -> Response:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        if mode != "subscribe" or challenge is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="challenge rejected")
        try:
            verifier.verify_challenge(token)
        except InvalidWebhookChallenge as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="challenge rejected",
            ) from exc
        return PlainTextResponse(challenge)

    async def receive_endpoint(request: Request) -> Response:
        content_type = request.headers.get("content-type", "").partition(";")[0].strip().lower()
        content_encoding = request.headers.get("content-encoding", "identity").strip().lower()
        if content_type != "application/json" or content_encoding != "identity":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="webhook media type rejected",
            )
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                announced = int(content_length)
            except ValueError:
                announced = -1
            if announced < 0 or announced > max_body_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="webhook body rejected",
                )
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > max_body_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="webhook body rejected",
                )
        raw_body = bytes(body)
        try:
            verifier.verify_signature(
                raw_body,
                request.headers.get("X-Hub-Signature-256"),
            )
        except InvalidWebhookSignature as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="webhook signature rejected",
            ) from exc
        try:
            envelope = decode_envelope(raw_body)
        except MalformedWebhookPayload as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="webhook payload rejected",
            ) from exc
        acceptance = await event_sink.accept(envelope)
        if acceptance not in {WebhookAcceptance.ACCEPTED, WebhookAcceptance.DUPLICATE}:
            raise RuntimeError("event sink returned an invalid acceptance")
        return Response(status_code=status.HTTP_200_OK)

    router.add_api_route(path, verify_endpoint, methods=["GET"], name="verify_meta_webhook")
    router.add_api_route(path, receive_endpoint, methods=["POST"], name="receive_meta_webhook")
    return router


__all__ = ["create_meta_webhook_router"]
