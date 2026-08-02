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
    max_events: int = 1_000,
    max_json_depth: int = 64,
) -> APIRouter:
    if not path.startswith("/"):
        raise ValueError("path must start with /")
    if not 1024 <= max_body_bytes <= 16_000_000:
        raise ValueError("max_body_bytes must be between 1024 and 16000000")
    if not 1 <= max_events <= 10_000:
        raise ValueError("max_events must be between 1 and 10000")
    if not 1 <= max_json_depth <= 256:
        raise ValueError("max_json_depth must be between 1 and 256")

    router = APIRouter(tags=["whatsapp-webhook"])

    async def verify_endpoint(request: Request) -> Response:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        if (
            mode != "subscribe"
            or challenge is None
            or not 1 <= len(challenge) <= 1_024
            or not challenge.isascii()
            or any(ord(character) < 32 or ord(character) == 127 for character in challenge)
        ):
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
            if len(chunk) > max_body_bytes - len(body):
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="webhook body rejected",
                )
            body.extend(chunk)
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
            envelope = decode_envelope(
                raw_body,
                max_body_bytes=max_body_bytes,
                max_events=max_events,
                max_json_depth=max_json_depth,
            )
        except MalformedWebhookPayload as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="webhook payload rejected",
            ) from exc
        try:
            acceptance = await event_sink.accept(envelope)
        except Exception:
            raise RuntimeError("event sink failed") from None
        if acceptance not in {WebhookAcceptance.ACCEPTED, WebhookAcceptance.DUPLICATE}:
            raise RuntimeError("event sink returned an invalid acceptance")
        return Response(status_code=status.HTTP_200_OK)

    router.add_api_route(path, verify_endpoint, methods=["GET"], name="verify_meta_webhook")
    router.add_api_route(path, receive_endpoint, methods=["POST"], name="receive_meta_webhook")
    return router


__all__ = ["create_meta_webhook_router"]
