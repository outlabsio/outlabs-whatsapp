"""Provider protocol."""

from __future__ import annotations

from typing import Protocol

from outlabs_whatsapp.commands import OutboundCommand
from outlabs_whatsapp.results import SendResult


class WhatsAppProvider(Protocol):
    async def send(self, command: OutboundCommand) -> SendResult: ...


__all__ = ["WhatsAppProvider"]
