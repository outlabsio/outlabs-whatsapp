from __future__ import annotations

import httpx
import pytest

from outlabs_whatsapp import (
    AuthenticationError,
    InvalidRecipientError,
    InvalidRequestError,
    InvalidTemplateError,
    PolicyError,
    ProviderUnavailableError,
    RateLimitedError,
)
from outlabs_whatsapp.meta.errors import error_from_response


def _response(status: int, *, retry_after: str | None = None) -> httpx.Response:
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    return httpx.Response(
        status,
        headers=headers,
        request=httpx.Request("POST", "https://graph.facebook.com/messages"),
    )


def test_known_meta_codes_map_to_closed_categories() -> None:
    assert isinstance(
        error_from_response(_response(400), {"error": {"code": 131026}}),
        InvalidRecipientError,
    )
    assert isinstance(
        error_from_response(_response(400), {"error": {"code": 132001}}),
        InvalidTemplateError,
    )
    assert isinstance(error_from_response(_response(400), {"error": {"code": 368}}), PolicyError)
    assert isinstance(
        error_from_response(_response(401), {"error": {"code": 190}}),
        AuthenticationError,
    )
    assert isinstance(
        error_from_response(_response(503), {"error": {"code": 131000}}),
        ProviderUnavailableError,
    )


def test_rate_limit_preserves_only_safe_fields() -> None:
    error = error_from_response(
        _response(429, retry_after="30"),
        {
            "error": {
                "code": 130429,
                "error_subcode": 7,
                "message": "echoed secret content",
                "fbtrace_id": "trace-1",
            }
        },
    )

    assert isinstance(error, RateLimitedError)
    assert error.retry_after_seconds == 30
    assert "echoed secret content" not in str(error)
    assert error.code == 130429
    assert error.subcode == 7


def test_all_known_error_families_and_http_fallbacks_are_closed() -> None:
    assert isinstance(
        error_from_response(_response(400), {"error": {"code": 10}}),
        AuthenticationError,
    )
    assert isinstance(
        error_from_response(_response(400), {"error": {"code": 17}}),
        RateLimitedError,
    )
    assert isinstance(error_from_response(_response(400), {"error": {"code": 131050}}), PolicyError)
    assert isinstance(
        error_from_response(_response(400), {"error": {"code": 132016}}),
        InvalidTemplateError,
    )
    assert isinstance(error_from_response(_response(403), None), AuthenticationError)
    assert isinstance(error_from_response(_response(500), None), ProviderUnavailableError)
    assert isinstance(error_from_response(_response(400), None), InvalidRequestError)


@pytest.mark.parametrize("retry_after", ["not-a-number", "-1", "2592001"])
def test_invalid_retry_after_values_are_discarded(retry_after: str) -> None:
    error = error_from_response(_response(429, retry_after=retry_after), None)

    assert isinstance(error, RateLimitedError)
    assert error.retry_after_seconds is None


def test_malformed_meta_error_fields_are_ignored() -> None:
    error = error_from_response(
        _response(400),
        {
            "error": {
                "code": True,
                "error_subcode": "7",
                "fbtrace_id": "",
                "message": "private provider text",
            }
        },
    )

    assert isinstance(error, InvalidRequestError)
    assert error.code is None
    assert error.subcode is None
    assert error.provider_trace_id is None
    assert "private provider text" not in str(error)


@pytest.mark.parametrize("payload", [None, [], {}, {"error": "not-an-object"}])
def test_non_error_shapes_are_treated_as_empty_error_metadata(payload: object) -> None:
    error = error_from_response(_response(400), payload)

    assert isinstance(error, InvalidRequestError)
    assert error.code is None
