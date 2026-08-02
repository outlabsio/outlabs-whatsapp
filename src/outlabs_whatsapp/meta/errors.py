"""Conservative Meta error decoding.

Meta may add codes at any time. Unknown client rejections remain terminal invalid-request errors;
unknown server responses remain ambiguous because the response does not prove the send was rejected
before Meta accepted it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

import httpx

from outlabs_whatsapp.errors import (
    AmbiguousSendError,
    AuthenticationError,
    InvalidRecipientError,
    InvalidRequestError,
    InvalidTemplateError,
    PolicyError,
    ProviderError,
    RateLimitedError,
)

_AUTH_CODES = {10, 190, 200}
_POLICY_CODES = {368, 130497, 131031, 131049, 131050}
_RECIPIENT_CODES = {131026, 131030}
_RATE_LIMIT_CODES = {4, 17, 32, 613, 130429, 131048}
_TEMPLATE_CODES = {132000, 132001, 132005, 132007, 132012, 132015, 132016}


@dataclass(frozen=True, slots=True)
class MetaErrorFields:
    code: int | None = None
    subcode: int | None = None
    provider_trace_id: str | None = None


class _ProviderErrorKwargs(TypedDict):
    code: int | None
    subcode: int | None
    http_status: int | None
    provider_trace_id: str | None


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def extract_meta_error(payload: object) -> MetaErrorFields:
    if not isinstance(payload, dict):
        return MetaErrorFields()
    error = payload.get("error")
    if not isinstance(error, dict):
        return MetaErrorFields()
    trace = error.get("fbtrace_id")
    safe_trace = (
        trace
        if isinstance(trace, str)
        and 1 <= len(trace) <= 256
        and all(33 <= ord(character) <= 126 for character in trace)
        else None
    )
    return MetaErrorFields(
        code=_integer(error.get("code")),
        subcode=_integer(error.get("error_subcode")),
        provider_trace_id=safe_trace,
    )


def _retry_after(response: httpx.Response) -> int | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if 0 <= parsed <= 2_592_000 else None


def error_from_response(response: httpx.Response, payload: Any) -> ProviderError:
    fields = extract_meta_error(payload)
    kwargs: _ProviderErrorKwargs = {
        "code": fields.code,
        "subcode": fields.subcode,
        "http_status": response.status_code,
        "provider_trace_id": fields.provider_trace_id,
    }
    if response.status_code == 429 or fields.code in _RATE_LIMIT_CODES:
        return RateLimitedError(retry_after_seconds=_retry_after(response), **kwargs)
    if fields.code in _POLICY_CODES:
        return PolicyError(**kwargs)
    if fields.code in _RECIPIENT_CODES:
        return InvalidRecipientError(**kwargs)
    if fields.code in _TEMPLATE_CODES:
        return InvalidTemplateError(**kwargs)
    if response.status_code in {401, 403} or fields.code in _AUTH_CODES:
        return AuthenticationError(**kwargs)
    if response.status_code >= 500:
        return AmbiguousSendError(**kwargs)
    return InvalidRequestError(**kwargs)


__all__ = ["MetaErrorFields", "error_from_response", "extract_meta_error"]
