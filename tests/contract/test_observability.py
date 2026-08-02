from __future__ import annotations

import logging

import httpx
import pytest

from outlabs_whatsapp import InvalidRequestError, MetaCloudClient, TextCommand, decode_envelope
from outlabs_whatsapp.testing import build_text_webhook


@pytest.mark.asyncio
async def test_default_package_execution_emits_no_logs_with_sensitive_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sensitive_values = {
        "PRIVATE-ACCESS-TOKEN",
        "15550001111",
        "PRIVATE-MESSAGE-CONTENT",
        "PRIVATE-PROVIDER-CONTENT",
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            request=request,
            json={
                "error": {
                    "code": 131000,
                    "message": "PRIVATE-PROVIDER-CONTENT",
                }
            },
        )

    caplog.set_level(logging.DEBUG, logger="outlabs_whatsapp")
    decode_envelope(build_text_webhook(body="PRIVATE-MESSAGE-CONTENT"))
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://graph.facebook.com",
    ) as http_client:
        client = MetaCloudClient(
            access_token="PRIVATE-ACCESS-TOKEN",
            phone_number_id="synthetic-phone-id",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(InvalidRequestError):
            await client.send(
                TextCommand(to="15550001111", body="PRIVATE-MESSAGE-CONTENT")
            )

    package_records = [
        record for record in caplog.records if record.name.startswith("outlabs_whatsapp")
    ]
    assert package_records == []
    rendered_records = "\n".join(record.getMessage() for record in caplog.records)
    assert all(value not in rendered_records for value in sensitive_values)
