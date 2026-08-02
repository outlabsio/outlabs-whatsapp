"""Normalized inbound webhook event contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class _EventModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


class DeliveryStatus(StrEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"
    UNKNOWN = "unknown"


class StatusError(_EventModel):
    code: int | None = None
    subcode: int | None = None


class EventBase(_EventModel):
    schema_version: Literal["1"] = "1"
    provider: Literal["meta"] = "meta"
    dedupe_key: str = Field(min_length=16, max_length=128)
    raw_payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    received_at: AwareDatetime
    occurred_at: AwareDatetime
    waba_id: str | None = Field(default=None, min_length=1, max_length=128)
    phone_number_id: str | None = Field(default=None, min_length=1, max_length=128)


class InboundTextEvent(EventBase):
    kind: Literal["inbound_text"] = "inbound_text"
    message_id: str = Field(min_length=1, max_length=512)
    from_number: str = Field(min_length=1, max_length=32, repr=False)
    body: str = Field(max_length=65536, repr=False)
    context_message_id: str | None = Field(default=None, min_length=1, max_length=512)


class InboundInteractiveEvent(EventBase):
    kind: Literal["inbound_interactive"] = "inbound_interactive"
    message_id: str = Field(min_length=1, max_length=512)
    from_number: str = Field(min_length=1, max_length=32, repr=False)
    interactive_type: Literal["button_reply", "list_reply", "button"]
    selection_id: str = Field(min_length=1, max_length=1024, repr=False)
    selection_title: str | None = Field(default=None, max_length=1024, repr=False)
    context_message_id: str | None = Field(default=None, min_length=1, max_length=512)


class MessageStatusEvent(EventBase):
    kind: Literal["message_status"] = "message_status"
    message_id: str = Field(min_length=1, max_length=512)
    status: DeliveryStatus
    recipient_id: str | None = Field(default=None, min_length=1, max_length=32, repr=False)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=512)
    pricing_category: str | None = Field(default=None, min_length=1, max_length=64)
    billable: bool | None = None
    errors: tuple[StatusError, ...] = Field(default=(), max_length=32)


class UnsupportedEvent(EventBase):
    kind: Literal["unsupported"] = "unsupported"
    event_type: str = Field(min_length=1, max_length=128)
    message_id: str | None = Field(default=None, min_length=1, max_length=512)


type NormalizedEvent = Annotated[
    InboundTextEvent | InboundInteractiveEvent | MessageStatusEvent | UnsupportedEvent,
    Field(discriminator="kind"),
]


__all__ = [
    "DeliveryStatus",
    "EventBase",
    "InboundInteractiveEvent",
    "InboundTextEvent",
    "MessageStatusEvent",
    "NormalizedEvent",
    "StatusError",
    "UnsupportedEvent",
]
