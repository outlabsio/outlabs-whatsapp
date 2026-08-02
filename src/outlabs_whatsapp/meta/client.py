"""Async direct Meta Cloud API client."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx
from pydantic import SecretStr

from outlabs_whatsapp.commands import OutboundCommand
from outlabs_whatsapp.errors import (
    AmbiguousSendError,
    MalformedProviderResponseError,
    ProviderUnavailableError,
)
from outlabs_whatsapp.meta.credentials import (
    AccessTokenProvider,
    coerce_token_provider,
    resolve_access_token,
)
from outlabs_whatsapp.meta.dto import command_to_meta_payload
from outlabs_whatsapp.meta.errors import error_from_response
from outlabs_whatsapp.results import SendResult

_GRAPH_VERSION = re.compile(r"^v\d+\.\d+$")
_PHONE_NUMBER_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class MetaCloudClient:
    """Stateless send client; durable retry and reconciliation belong to the host."""

    def __init__(
        self,
        *,
        access_token: str | SecretStr | AccessTokenProvider,
        phone_number_id: str,
        graph_version: str,
        http_client: httpx.AsyncClient | None = None,
        base_url: str = "https://graph.facebook.com",
        timeout_seconds: float = 15.0,
    ) -> None:
        if _GRAPH_VERSION.fullmatch(graph_version) is None:
            raise ValueError("graph_version must look like vNN.N")
        if _PHONE_NUMBER_ID.fullmatch(phone_number_id) is None:
            raise ValueError("phone_number_id contains invalid characters")
        if not 0 < timeout_seconds <= 120:
            raise ValueError("timeout_seconds must be between 0 and 120")
        parsed_base_url = httpx.URL(base_url)
        if (
            parsed_base_url.scheme != "https"
            or parsed_base_url.host is None
            or parsed_base_url.username
            or parsed_base_url.password
            or parsed_base_url.query
            or parsed_base_url.fragment
            or parsed_base_url.path not in {"", "/"}
        ):
            raise ValueError("base_url must be an HTTPS origin without credentials, path, or query")
        self._token_provider = coerce_token_provider(access_token)
        self.phone_number_id = phone_number_id
        self.graph_version = graph_version
        self._timeout = httpx.Timeout(timeout_seconds)
        self._owns_client = http_client is None
        self._closed = False
        self._http = http_client or httpx.AsyncClient(base_url=str(parsed_base_url).rstrip("/"))

    def __repr__(self) -> str:
        return (
            "MetaCloudClient(access_token=***, "
            f"phone_number_id={self.phone_number_id!r}, graph_version={self.graph_version!r})"
        )

    async def __aenter__(self) -> MetaCloudClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and not self._closed:
            await self._http.aclose()
        self._closed = True

    async def send(self, command: OutboundCommand) -> SendResult:
        if self._closed:
            raise RuntimeError("MetaCloudClient is closed")
        token = await resolve_access_token(self._token_provider)
        payload = command_to_meta_payload(command)
        try:
            response = await self._http.post(
                f"/{self.graph_version}/{self.phone_number_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=self._timeout,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
            raise ProviderUnavailableError() from exc
        except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError) as exc:
            raise AmbiguousSendError() from exc
        except httpx.TransportError as exc:
            raise AmbiguousSendError() from exc

        try:
            decoded = response.json()
        except ValueError as exc:
            if response.is_error:
                decoded = None
            else:
                raise MalformedProviderResponseError(http_status=response.status_code) from exc

        if response.is_error:
            raise error_from_response(response, decoded)
        if not isinstance(decoded, dict):
            raise MalformedProviderResponseError(http_status=response.status_code)
        messages = decoded.get("messages")
        if not isinstance(messages, list) or not messages or not isinstance(messages[0], dict):
            raise MalformedProviderResponseError(http_status=response.status_code)
        message_id = messages[0].get("id")
        if not isinstance(message_id, str) or not message_id:
            raise MalformedProviderResponseError(http_status=response.status_code)
        trace = response.headers.get("X-FB-Trace-ID")
        return SendResult(
            message_id=message_id,
            phone_number_id=self.phone_number_id,
            accepted_at=datetime.now(UTC),
            host_reference=command.host_reference,
            provider_trace_id=trace if trace else None,
        )


__all__ = ["MetaCloudClient"]
