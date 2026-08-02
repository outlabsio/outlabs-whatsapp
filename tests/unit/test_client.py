from __future__ import annotations

import httpx
import pytest

from outlabs_whatsapp import (
    AmbiguousSendError,
    InvalidRequestError,
    MalformedProviderResponseError,
    MetaCloudClient,
    ProviderUnavailableError,
    RateLimitedError,
    TemplateCommand,
)


def _command() -> TemplateCommand:
    return TemplateCommand(
        to="15550001111",
        name="portal_access_ready",
        language_code="es_AR",
    )


@pytest.mark.asyncio
async def test_meta_client_sends_and_returns_message_id() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v99.0/phone-1/messages"
        assert request.headers["Authorization"] == "Bearer secret-token"
        return httpx.Response(
            200,
            headers={"X-FB-Trace-ID": "trace-1"},
            json={"messages": [{"id": "wamid.accepted"}]},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://graph.facebook.com",
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        result = await client.send(
            TemplateCommand(
                to="15550001111",
                name="portal_access_ready",
                language_code="es_AR",
                host_reference="intent-1",
            )
        )

    assert result.message_id == "wamid.accepted"
    assert result.host_reference == "intent-1"
    assert result.provider_trace_id == "trace-1"
    assert "secret-token" not in repr(client)


@pytest.mark.asyncio
async def test_meta_client_maps_rate_limit() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            request=request,
            headers={"Retry-After": "20"},
            json={"error": {"code": 130429}},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(RateLimitedError) as captured:
            await client.send(
                TemplateCommand(
                    to="15550001111",
                    name="portal_access_ready",
                    language_code="es_AR",
                )
            )

    assert captured.value.retry_after_seconds == 20


@pytest.mark.asyncio
async def test_read_timeout_is_ambiguous() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("synthetic", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(AmbiguousSendError):
            await client.send(
                TemplateCommand(
                    to="15550001111",
                    name="portal_access_ready",
                    language_code="es_AR",
                )
            )


@pytest.mark.asyncio
async def test_connect_failure_is_retryable_unavailable() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(ProviderUnavailableError):
            await client.send(
                TemplateCommand(
                    to="15550001111",
                    name="portal_access_ready",
                    language_code="es_AR",
                )
            )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"graph_version": "latest"}, "graph_version"),
        ({"phone_number_id": "phone/1"}, "phone_number_id"),
        ({"timeout_seconds": 0}, "timeout_seconds"),
        ({"timeout_seconds": 121}, "timeout_seconds"),
        ({"base_url": "http://graph.facebook.com"}, "HTTPS origin"),
        ({"base_url": "https://user:pass@graph.facebook.com"}, "HTTPS origin"),
        ({"base_url": "https://graph.facebook.com/path"}, "HTTPS origin"),
        ({"base_url": "https://graph.facebook.com?token=bad"}, "HTTPS origin"),
    ],
)
def test_client_rejects_unsafe_configuration(
    overrides: dict[str, object], message: str
) -> None:
    kwargs: dict[str, object] = {
        "access_token": "secret-token",
        "phone_number_id": "phone-1",
        "graph_version": "v99.0",
    }
    kwargs.update(overrides)

    with pytest.raises(ValueError, match=message):
        MetaCloudClient(**kwargs)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_rotating_token_provider_is_resolved_for_every_send() -> None:
    calls = 0
    authorization: list[str] = []

    def token_provider() -> str:
        nonlocal calls
        calls += 1
        return f"token-{calls}"

    async def handler(request: httpx.Request) -> httpx.Response:
        authorization.append(request.headers["Authorization"])
        return httpx.Response(200, json={"messages": [{"id": f"wamid.{calls}"}]})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token=token_provider,
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        await client.send(_command())
        await client.send(_command())

    assert authorization == ["Bearer token-1", "Bearer token-2"]


@pytest.mark.asyncio
async def test_client_never_closes_injected_http_client() -> None:
    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200)),
        base_url="https://graph.facebook.com",
    )
    client = MetaCloudClient(
        access_token="secret-token",
        phone_number_id="phone-1",
        graph_version="v99.0",
        http_client=http_client,
    )

    await client.aclose()

    assert not http_client.is_closed
    with pytest.raises(RuntimeError, match="closed"):
        await client.send(_command())
    await http_client.aclose()


@pytest.mark.asyncio
async def test_owned_client_close_is_idempotent() -> None:
    client = MetaCloudClient(
        access_token="secret-token",
        phone_number_id="phone-1",
        graph_version="v99.0",
    )

    await client.aclose()
    await client.aclose()

    with pytest.raises(RuntimeError, match="closed"):
        await client.send(_command())


@pytest.mark.asyncio
async def test_async_context_manager_closes_owned_client() -> None:
    async with MetaCloudClient(
        access_token="secret-token",
        phone_number_id="phone-1",
        graph_version="v99.0",
    ) as client:
        assert "access_token=***" in repr(client)

    with pytest.raises(RuntimeError, match="closed"):
        await client.send(_command())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"messages": []},
        {"messages": ["not-an-object"]},
        {"messages": [{}]},
        {"messages": [{"id": ""}]},
    ],
)
async def test_success_responses_require_a_nonempty_message_id(payload: object) -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(MalformedProviderResponseError):
            await client.send(_command())


@pytest.mark.asyncio
async def test_non_json_success_and_error_responses_remain_safe() -> None:
    responses = iter(
        [
            httpx.Response(200, text="private upstream body"),
            httpx.Response(400, text="private upstream error"),
        ]
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return next(responses)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(MalformedProviderResponseError) as malformed:
            await client.send(_command())
        with pytest.raises(InvalidRequestError) as rejected:
            await client.send(_command())

    assert "private upstream body" not in str(malformed.value)
    assert "private upstream error" not in str(rejected.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception_type", "expected_error"),
    [
        (httpx.ConnectTimeout, ProviderUnavailableError),
        (httpx.PoolTimeout, ProviderUnavailableError),
        (httpx.WriteTimeout, AmbiguousSendError),
        (httpx.RemoteProtocolError, AmbiguousSendError),
        (httpx.ProxyError, AmbiguousSendError),
    ],
)
async def test_transport_failures_have_conservative_retry_semantics(
    exception_type: type[httpx.TransportError],
    expected_error: type[Exception],
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise exception_type("synthetic", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://graph.facebook.com"
    ) as http_client:
        client = MetaCloudClient(
            access_token="secret-token",
            phone_number_id="phone-1",
            graph_version="v99.0",
            http_client=http_client,
        )
        with pytest.raises(expected_error):
            await client.send(_command())
