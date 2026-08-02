from __future__ import annotations

import os

import pytest

from outlabs_whatsapp import MetaCloudClient, TemplateCommand

_RUN_GUARD = "I_UNDERSTAND_THIS_SENDS_A_WHATSAPP_MESSAGE"


@pytest.mark.manual
@pytest.mark.asyncio
async def test_synthetic_hello_world_send_against_meta_test_waba() -> None:
    if os.environ.get("OUTLABS_WHATSAPP_RUN_META_SMOKE") != _RUN_GUARD:
        pytest.skip("manual Meta smoke is explicitly disabled")
    if os.environ.get("META_SMOKE_ASSERT_SYNTHETIC") != "YES":
        pytest.fail("META_SMOKE_ASSERT_SYNTHETIC=YES is required")

    required = {
        name: os.environ.get(name)
        for name in (
            "META_WHATSAPP_ACCESS_TOKEN",
            "META_WHATSAPP_PHONE_NUMBER_ID",
            "META_GRAPH_VERSION",
            "META_TEST_RECIPIENT",
        )
    }
    missing = sorted(name for name, value in required.items() if not value)
    if missing:
        pytest.fail(f"missing manual Meta smoke configuration names: {', '.join(missing)}")

    async with MetaCloudClient(
        access_token=required["META_WHATSAPP_ACCESS_TOKEN"],  # type: ignore[arg-type]
        phone_number_id=required["META_WHATSAPP_PHONE_NUMBER_ID"],  # type: ignore[arg-type]
        graph_version=required["META_GRAPH_VERSION"],  # type: ignore[arg-type]
    ) as client:
        result = await client.send(
            TemplateCommand(
                to=required["META_TEST_RECIPIENT"],  # type: ignore[arg-type]
                name="hello_world",
                language_code="en_US",
                host_reference="synthetic-manual-smoke",
            )
        )

    assert result.message_id.startswith("wamid.")
    assert result.host_reference == "synthetic-manual-smoke"
