"""Provider result contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class SendResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    provider: Literal["meta"] = "meta"
    message_id: str = Field(min_length=1, max_length=512)
    phone_number_id: str = Field(min_length=1, max_length=128)
    accepted_at: AwareDatetime
    host_reference: str | None = Field(default=None, min_length=1, max_length=256)
    provider_trace_id: str | None = Field(default=None, min_length=1, max_length=256)


__all__ = ["SendResult"]
