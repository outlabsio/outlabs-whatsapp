from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import SecretStr

from outlabs_whatsapp.meta.credentials import (
    StaticAccessToken,
    coerce_token_provider,
    resolve_access_token,
)


@pytest.mark.parametrize(
    "token",
    ["", " leading", "trailing ", "line\nbreak", "tab\tinside", "non-ascii-ñ"],
)
def test_static_tokens_reject_header_unsafe_values(token: str) -> None:
    with pytest.raises(ValueError, match="access token"):
        StaticAccessToken(token)


def test_static_token_repr_never_exposes_secret() -> None:
    token = StaticAccessToken(SecretStr("private-token"))

    assert "private-token" not in repr(token)


@pytest.mark.asyncio
async def test_resolver_supports_sync_and_async_rotation() -> None:
    calls = 0

    async def rotating_provider() -> SecretStr:
        nonlocal calls
        calls += 1
        return SecretStr(f"token-{calls}")

    assert await resolve_access_token(rotating_provider) == "token-1"
    assert await resolve_access_token(rotating_provider) == "token-2"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider",
    [
        lambda: "bad token",
        lambda: "bad\r\ntoken",
        lambda: "",
        lambda: 123,
    ],
)
async def test_resolver_rejects_invalid_provider_results(provider: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match="provider result"):
        await resolve_access_token(provider)  # type: ignore[arg-type]


def test_coercion_rejects_non_callable_objects() -> None:
    with pytest.raises(TypeError, match="callable provider"):
        coerce_token_provider(object())  # type: ignore[arg-type]


def test_coercion_preserves_callable_provider() -> None:
    def provider() -> str:
        return "token-value"

    assert coerce_token_provider(provider) is provider
