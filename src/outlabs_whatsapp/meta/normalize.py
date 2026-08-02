"""Normalize signed Meta webhook payloads into versioned package events."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, TypedDict, cast

from outlabs_whatsapp.events import (
    DeliveryStatus,
    InboundInteractiveEvent,
    InboundTextEvent,
    MessageStatusEvent,
    NormalizedEvent,
    StatusError,
    UnsupportedEvent,
)


class _EventLimitExceeded(Exception):
    pass


def _text(value: object, *, max_length: int | None = None) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if max_length is not None and len(value) > max_length:
        return None
    return value


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _timestamp(value: object, fallback: datetime) -> datetime:
    if isinstance(value, int) and not isinstance(value, bool):
        seconds = value
    else:
        raw = _text(value, max_length=64)
        if raw is None:
            return fallback
        try:
            seconds = int(raw)
        except ValueError:
            return fallback
    try:
        return datetime.fromtimestamp(seconds, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return fallback


def _dedupe(*parts: object) -> str:
    safe_parts: list[str] = []
    for part in parts:
        if part is None:
            text = ""
        elif isinstance(part, (str, int, bool)):
            text = str(part)
        else:
            text = f"<{type(part).__name__}>"
        if len(text) > 1024:
            text = f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
        safe_parts.append(text)
    joined = "\x1f".join(safe_parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


class _EventFields(TypedDict):
    dedupe_key: str
    raw_payload_sha256: str
    received_at: datetime
    occurred_at: datetime
    waba_id: str | None
    phone_number_id: str | None


def _context_message_id(message: Mapping[str, Any]) -> str | None:
    context = message.get("context")
    return _text(context.get("id"), max_length=512) if isinstance(context, Mapping) else None


def _status_errors(status: Mapping[str, Any]) -> tuple[StatusError, ...]:
    raw_errors = status.get("errors")
    if not isinstance(raw_errors, Sequence) or isinstance(raw_errors, (str, bytes)):
        return ()
    result: list[StatusError] = []
    for raw in raw_errors[:32]:
        if isinstance(raw, Mapping):
            result.append(
                StatusError(
                    code=_integer(raw.get("code")),
                    subcode=_integer(raw.get("error_subcode")),
                )
            )
    return tuple(result)


def _message_event(
    message: Mapping[str, Any],
    *,
    waba_id: str | None,
    phone_number_id: str | None,
    raw_payload_sha256: str,
    received_at: datetime,
) -> NormalizedEvent:
    message_id = _text(message.get("id"), max_length=512)
    sender = _text(message.get("from"), max_length=32)
    message_type = _text(message.get("type"), max_length=120) or "unknown"
    occurred_at = _timestamp(message.get("timestamp"), received_at)
    common: _EventFields = {
        "dedupe_key": _dedupe("message", message_id, message_type),
        "raw_payload_sha256": raw_payload_sha256,
        "received_at": received_at,
        "occurred_at": occurred_at,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
    }
    if message_type == "text" and message_id and sender:
        text = message.get("text")
        body = _text(text.get("body"), max_length=65536) if isinstance(text, Mapping) else None
        if body is not None:
            return InboundTextEvent(
                **common,
                message_id=message_id,
                from_number=sender,
                body=body,
                context_message_id=_context_message_id(message),
            )

    if message_type == "interactive" and message_id and sender:
        interactive = message.get("interactive")
        if isinstance(interactive, Mapping):
            interactive_type = _text(interactive.get("type"), max_length=32)
            reply = interactive.get(interactive_type) if interactive_type else None
            if interactive_type in {"button_reply", "list_reply"} and isinstance(reply, Mapping):
                selection_id = _text(reply.get("id"), max_length=1024)
                if selection_id:
                    return InboundInteractiveEvent(
                        **common,
                        message_id=message_id,
                        from_number=sender,
                        interactive_type=cast(
                            Literal["button_reply", "list_reply"], interactive_type
                        ),
                        selection_id=selection_id,
                        selection_title=_text(reply.get("title"), max_length=1024),
                        context_message_id=_context_message_id(message),
                    )

    if message_type == "button" and message_id and sender:
        button = message.get("button")
        if isinstance(button, Mapping):
            selection_id = _text(button.get("payload"), max_length=1024) or _text(
                button.get("text"), max_length=1024
            )
            if selection_id:
                return InboundInteractiveEvent(
                    **common,
                    message_id=message_id,
                    from_number=sender,
                    interactive_type="button",
                    selection_id=selection_id,
                    selection_title=_text(button.get("text"), max_length=1024),
                    context_message_id=_context_message_id(message),
                )

    return UnsupportedEvent(
        **common,
        event_type=f"message:{message_type}",
        message_id=message_id,
    )


def _status_event(
    status: Mapping[str, Any],
    *,
    waba_id: str | None,
    phone_number_id: str | None,
    raw_payload_sha256: str,
    received_at: datetime,
) -> NormalizedEvent:
    message_id = _text(status.get("id"), max_length=512)
    status_text = _text(status.get("status"), max_length=120) or "unknown"
    occurred_at = _timestamp(status.get("timestamp"), received_at)
    if message_id:
        try:
            normalized_status = DeliveryStatus(status_text)
        except ValueError:
            normalized_status = DeliveryStatus.UNKNOWN
        conversation = status.get("conversation")
        pricing = status.get("pricing")
        conversation_id = (
            _text(conversation.get("id"), max_length=512)
            if isinstance(conversation, Mapping)
            else None
        )
        pricing_category = (
            _text(pricing.get("category"), max_length=64)
            if isinstance(pricing, Mapping)
            else None
        )
        billable_raw = pricing.get("billable") if isinstance(pricing, Mapping) else None
        return MessageStatusEvent(
            dedupe_key=_dedupe("status", message_id, status_text, status.get("timestamp")),
            raw_payload_sha256=raw_payload_sha256,
            received_at=received_at,
            occurred_at=occurred_at,
            waba_id=waba_id,
            phone_number_id=phone_number_id,
            message_id=message_id,
            status=normalized_status,
            recipient_id=_text(status.get("recipient_id"), max_length=32),
            conversation_id=conversation_id,
            pricing_category=pricing_category,
            billable=billable_raw if isinstance(billable_raw, bool) else None,
            errors=_status_errors(status),
        )
    return UnsupportedEvent(
        dedupe_key=_dedupe("status", status_text, status.get("timestamp"), raw_payload_sha256),
        raw_payload_sha256=raw_payload_sha256,
        received_at=received_at,
        occurred_at=occurred_at,
        waba_id=waba_id,
        phone_number_id=phone_number_id,
        event_type=f"status:{status_text}",
    )


def normalize_payload(
    payload: Mapping[str, Any],
    *,
    raw_payload_sha256: str,
    received_at: datetime,
    max_events: int = 1_000,
) -> tuple[NormalizedEvent, ...]:
    if not 1 <= max_events <= 10_000:
        raise ValueError("max_events must be between 1 and 10000")
    events: list[NormalizedEvent] = []

    def append_event(event: NormalizedEvent) -> None:
        if len(events) >= max_events:
            raise _EventLimitExceeded
        events.append(event)

    entries = payload.get("entry")
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        entries = ()

    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        waba_id = _text(entry.get("id"), max_length=128)
        changes = entry.get("changes")
        if not isinstance(changes, Sequence) or isinstance(changes, (str, bytes)):
            continue
        for change in changes:
            if not isinstance(change, Mapping):
                continue
            field = _text(change.get("field"), max_length=121) or "unknown"
            value = change.get("value")
            if not isinstance(value, Mapping):
                continue
            metadata = value.get("metadata")
            phone_number_id = (
                _text(metadata.get("phone_number_id"), max_length=128)
                if isinstance(metadata, Mapping)
                else None
            )
            before = len(events)
            messages = value.get("messages")
            if isinstance(messages, Sequence) and not isinstance(messages, (str, bytes)):
                for message in messages:
                    if isinstance(message, Mapping):
                        append_event(
                            _message_event(
                                message,
                                waba_id=waba_id,
                                phone_number_id=phone_number_id,
                                raw_payload_sha256=raw_payload_sha256,
                                received_at=received_at,
                            )
                        )
            statuses = value.get("statuses")
            if isinstance(statuses, Sequence) and not isinstance(statuses, (str, bytes)):
                for status in statuses:
                    if isinstance(status, Mapping):
                        append_event(
                            _status_event(
                                status,
                                waba_id=waba_id,
                                phone_number_id=phone_number_id,
                                raw_payload_sha256=raw_payload_sha256,
                                received_at=received_at,
                            )
                        )
            if len(events) == before:
                append_event(
                    UnsupportedEvent(
                        dedupe_key=_dedupe(
                            "change", waba_id, phone_number_id, field, raw_payload_sha256
                        ),
                        raw_payload_sha256=raw_payload_sha256,
                        received_at=received_at,
                        occurred_at=received_at,
                        waba_id=waba_id,
                        phone_number_id=phone_number_id,
                        event_type=f"change:{field}",
                    )
                )

    if not events:
        append_event(
            UnsupportedEvent(
                dedupe_key=_dedupe("payload", raw_payload_sha256),
                raw_payload_sha256=raw_payload_sha256,
                received_at=received_at,
                occurred_at=received_at,
                event_type=(
                    f"object:{_text(payload.get('object'), max_length=121) or 'unknown'}"
                ),
            )
        )
    return tuple(events)


__all__ = ["normalize_payload"]
