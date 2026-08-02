"""Rotatable Meta access-token providers."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable
from typing import Protocol

from pydantic import SecretStr

type TokenValue = str | SecretStr
type TokenResult = TokenValue | Awaitable[TokenValue]


class AccessTokenProvider(Protocol):
    def __call__(self) -> TokenResult: ...


class StaticAccessToken:
    __slots__ = ("_token",)

    def __init__(self, token: str | SecretStr) -> None:
        value = token.get_secret_value() if isinstance(token, SecretStr) else token
        self._token = SecretStr(_validated_token(value, source="access token"))

    def __call__(self) -> SecretStr:
        return self._token

    def __repr__(self) -> str:
        return "StaticAccessToken(***)"


async def resolve_access_token(provider: AccessTokenProvider) -> str:
    result = provider()
    resolved = await result if inspect.isawaitable(result) else result
    token = resolved.get_secret_value() if isinstance(resolved, SecretStr) else resolved
    return _validated_token(token, source="access token provider result")


def _validated_token(value: object, *, source: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{source} must be a non-empty string")
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        raise ValueError(f"{source} must contain only visible ASCII characters")
    return value


def coerce_token_provider(
    value: str | SecretStr | AccessTokenProvider,
) -> AccessTokenProvider:
    if isinstance(value, (str, SecretStr)):
        return StaticAccessToken(value)
    if not callable(value):
        raise TypeError("access token must be a string, SecretStr, or callable provider")
    return value


__all__ = [
    "AccessTokenProvider",
    "StaticAccessToken",
    "TokenResult",
    "TokenValue",
    "coerce_token_provider",
    "resolve_access_token",
]
