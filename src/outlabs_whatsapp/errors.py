"""Safe, closed error categories for provider and webhook failures."""

from __future__ import annotations


class WhatsAppError(Exception):
    """Base package error whose string representation is safe to record."""


class ProviderError(WhatsAppError):
    default_message = "WhatsApp provider rejected the operation"

    def __init__(
        self,
        *,
        code: int | None = None,
        subcode: int | None = None,
        http_status: int | None = None,
        provider_trace_id: str | None = None,
    ) -> None:
        self.code = code
        self.subcode = subcode
        self.http_status = http_status
        self.provider_trace_id = provider_trace_id
        parts = [self.default_message]
        if code is not None:
            parts.append(f"code={code}")
        if subcode is not None:
            parts.append(f"subcode={subcode}")
        if http_status is not None:
            parts.append(f"status={http_status}")
        super().__init__("; ".join(parts))


class AuthenticationError(ProviderError):
    default_message = "WhatsApp provider authentication failed"


class PolicyError(ProviderError):
    default_message = "WhatsApp provider policy rejected the operation"


class InvalidRecipientError(ProviderError):
    default_message = "WhatsApp provider rejected the recipient"


class InvalidTemplateError(ProviderError):
    default_message = "WhatsApp provider rejected the template"


class InvalidRequestError(ProviderError):
    default_message = "WhatsApp provider rejected the request"


class RateLimitedError(ProviderError):
    default_message = "WhatsApp provider rate limited the operation"

    def __init__(
        self,
        *,
        retry_after_seconds: int | None = None,
        code: int | None = None,
        subcode: int | None = None,
        http_status: int | None = None,
        provider_trace_id: str | None = None,
    ) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            code=code,
            subcode=subcode,
            http_status=http_status,
            provider_trace_id=provider_trace_id,
        )


class ProviderUnavailableError(ProviderError):
    default_message = "WhatsApp provider is temporarily unavailable"


class AmbiguousSendError(ProviderError):
    default_message = "WhatsApp send outcome is ambiguous; do not retry automatically"


class MalformedProviderResponseError(ProviderError):
    default_message = "WhatsApp provider returned an invalid response"


class WebhookError(WhatsAppError):
    """Base webhook verification or decoding error."""


class InvalidWebhookSignature(WebhookError):
    def __init__(self) -> None:
        super().__init__("invalid WhatsApp webhook signature")


class InvalidWebhookChallenge(WebhookError):
    def __init__(self) -> None:
        super().__init__("invalid WhatsApp webhook challenge")


class MalformedWebhookPayload(WebhookError):
    def __init__(self) -> None:
        super().__init__("malformed WhatsApp webhook payload")


__all__ = [
    "AmbiguousSendError",
    "AuthenticationError",
    "InvalidRecipientError",
    "InvalidRequestError",
    "InvalidTemplateError",
    "InvalidWebhookChallenge",
    "InvalidWebhookSignature",
    "MalformedProviderResponseError",
    "MalformedWebhookPayload",
    "PolicyError",
    "ProviderError",
    "ProviderUnavailableError",
    "RateLimitedError",
    "WebhookError",
    "WhatsAppError",
]
