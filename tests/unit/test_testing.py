from __future__ import annotations

from datetime import UTC, datetime

import pytest

from outlabs_whatsapp import PolicyError, SendResult, TextCommand
from outlabs_whatsapp.testing import FakeWhatsAppProvider


@pytest.mark.asyncio
async def test_fake_records_commands_without_sensitive_assertion_output() -> None:
    fake = FakeWhatsAppProvider()
    await fake.send(TextCommand(to="15550001111", body="private", host_reference="intent-1"))

    matches = fake.assert_sent(kind="text")

    assert len(matches) == 1


@pytest.mark.asyncio
async def test_fake_queues_safe_errors() -> None:
    fake = FakeWhatsAppProvider()
    fake.queue_error(PolicyError(code=368))

    with pytest.raises(PolicyError):
        await fake.send(TextCommand(to="15550001111", body="private"))


@pytest.mark.asyncio
async def test_fake_returns_queued_result() -> None:
    fake = FakeWhatsAppProvider()
    queued = SendResult(
        message_id="wamid.queued",
        phone_number_id="test-phone-number-id",
        accepted_at=datetime(2026, 8, 2, tzinfo=UTC),
    )
    fake.queue_result(queued)

    result = await fake.send(TextCommand(to="15550001111", body="private"))

    assert result is queued


def test_fake_assertion_error_is_safe() -> None:
    fake = FakeWhatsAppProvider()

    with pytest.raises(AssertionError, match="expected 1 WhatsApp command") as captured:
        fake.assert_sent(kind="text")

    assert "private" not in str(captured.value)
