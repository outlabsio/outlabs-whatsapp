"""No-network provider and webhook sink fakes for consumer tests."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime

from outlabs_whatsapp.commands import OutboundCommand
from outlabs_whatsapp.errors import WhatsAppError
from outlabs_whatsapp.results import SendResult
from outlabs_whatsapp.webhooks import WebhookAcceptance, WebhookEnvelope


class FakeWhatsAppProvider:
    def __init__(self, *, phone_number_id: str = "test-phone-number-id") -> None:
        self.phone_number_id = phone_number_id
        self.sent: list[OutboundCommand] = []
        self._outcomes: deque[SendResult | WhatsAppError] = deque()

    def queue_result(self, result: SendResult) -> None:
        self._outcomes.append(result)

    def queue_error(self, error: WhatsAppError) -> None:
        self._outcomes.append(error)

    async def send(self, command: OutboundCommand) -> SendResult:
        self.sent.append(command)
        if self._outcomes:
            outcome = self._outcomes.popleft()
            if isinstance(outcome, WhatsAppError):
                raise outcome
            return outcome
        return SendResult(
            message_id=f"wamid.test.{len(self.sent)}",
            phone_number_id=self.phone_number_id,
            accepted_at=datetime.now(UTC),
            host_reference=command.host_reference,
        )

    def assert_sent(self, *, kind: str, count: int = 1) -> tuple[OutboundCommand, ...]:
        matches = tuple(command for command in self.sent if command.kind == kind)
        if len(matches) != count:
            raise AssertionError(
                f"expected {count} WhatsApp command(s) of kind {kind!r}; got {len(matches)}"
            )
        return matches


class FakeEventSink:
    def __init__(self, *, acceptance: WebhookAcceptance = WebhookAcceptance.ACCEPTED) -> None:
        self.acceptance = acceptance
        self.envelopes: list[WebhookEnvelope] = []

    async def accept(self, envelope: WebhookEnvelope) -> WebhookAcceptance:
        self.envelopes.append(envelope)
        return self.acceptance


__all__ = ["FakeEventSink", "FakeWhatsAppProvider"]
