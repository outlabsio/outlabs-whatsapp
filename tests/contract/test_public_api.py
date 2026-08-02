from __future__ import annotations

import inspect

import outlabs_whatsapp
import outlabs_whatsapp.fastapi
import outlabs_whatsapp.meta
import outlabs_whatsapp.testing
from outlabs_whatsapp import (
    InboundInteractiveEvent,
    InboundTextEvent,
    InteractiveButtonsCommand,
    MessageStatusEvent,
    ReplyButton,
    SendResult,
    TemplateBodyComponent,
    TemplateButtonComponent,
    TemplateCommand,
    TemplatePayloadParameter,
    TemplateTextParameter,
    TextCommand,
    UnsupportedEvent,
    WebhookEnvelope,
    WebhookVerifier,
    WhatsAppProvider,
    decode_envelope,
    payload_sha256,
    signature_for,
    verify_challenge,
    verify_signature,
)
from outlabs_whatsapp.fastapi import create_meta_webhook_router
from outlabs_whatsapp.meta import MetaCloudClient, StaticAccessToken

EXPECTED_ROOT_EXPORTS = (
    "AmbiguousSendError",
    "AuthenticationError",
    "DeliveryStatus",
    "EventSink",
    "InboundInteractiveEvent",
    "InboundTextEvent",
    "InteractiveButtonsCommand",
    "InvalidRecipientError",
    "InvalidRequestError",
    "InvalidTemplateError",
    "InvalidWebhookChallenge",
    "InvalidWebhookSignature",
    "MalformedProviderResponseError",
    "MalformedWebhookPayload",
    "MessageStatusEvent",
    "MetaCloudClient",
    "NormalizedEvent",
    "OutboundCommand",
    "PolicyError",
    "ProviderError",
    "ProviderUnavailableError",
    "RateLimitedError",
    "ReplyButton",
    "SendResult",
    "TemplateBodyComponent",
    "TemplateButtonComponent",
    "TemplateCommand",
    "TemplatePayloadParameter",
    "TemplateTextParameter",
    "TextCommand",
    "UnsupportedEvent",
    "WebhookAcceptance",
    "WebhookEnvelope",
    "WebhookError",
    "WebhookVerifier",
    "WhatsAppError",
    "WhatsAppProvider",
    "decode_envelope",
    "payload_sha256",
    "signature_for",
    "verify_challenge",
    "verify_signature",
)

EXPECTED_MODEL_FIELDS = {
    TextCommand: ("kind", "to", "body", "preview_url", "reply_to_message_id", "host_reference"),
    TemplateTextParameter: ("type", "text"),
    TemplatePayloadParameter: ("type", "payload"),
    TemplateBodyComponent: ("type", "parameters"),
    TemplateButtonComponent: ("type", "sub_type", "index", "parameters"),
    TemplateCommand: ("kind", "to", "name", "language_code", "components", "host_reference"),
    ReplyButton: ("id", "title"),
    InteractiveButtonsCommand: (
        "kind",
        "to",
        "body",
        "buttons",
        "header",
        "footer",
        "host_reference",
    ),
    SendResult: (
        "provider",
        "message_id",
        "phone_number_id",
        "accepted_at",
        "host_reference",
        "provider_trace_id",
    ),
    InboundTextEvent: (
        "schema_version",
        "provider",
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "waba_id",
        "phone_number_id",
        "kind",
        "message_id",
        "from_number",
        "body",
        "context_message_id",
    ),
    InboundInteractiveEvent: (
        "schema_version",
        "provider",
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "waba_id",
        "phone_number_id",
        "kind",
        "message_id",
        "from_number",
        "interactive_type",
        "selection_id",
        "selection_title",
        "context_message_id",
    ),
    MessageStatusEvent: (
        "schema_version",
        "provider",
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "waba_id",
        "phone_number_id",
        "kind",
        "message_id",
        "status",
        "recipient_id",
        "conversation_id",
        "pricing_category",
        "billable",
        "errors",
    ),
    UnsupportedEvent: (
        "schema_version",
        "provider",
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "waba_id",
        "phone_number_id",
        "kind",
        "event_type",
        "message_id",
    ),
    WebhookEnvelope: ("events", "raw_body", "raw_payload_sha256", "received_at"),
}

EXPECTED_REQUIRED_FIELDS = {
    TextCommand: {"to", "body"},
    TemplateTextParameter: {"text"},
    TemplatePayloadParameter: {"payload"},
    TemplateBodyComponent: set(),
    TemplateButtonComponent: {"sub_type", "index", "parameters"},
    TemplateCommand: {"to", "name", "language_code"},
    ReplyButton: {"id", "title"},
    InteractiveButtonsCommand: {"to", "body", "buttons"},
    SendResult: {"message_id", "phone_number_id", "accepted_at"},
    InboundTextEvent: {
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "message_id",
        "from_number",
        "body",
    },
    InboundInteractiveEvent: {
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "message_id",
        "from_number",
        "interactive_type",
        "selection_id",
    },
    MessageStatusEvent: {
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "message_id",
        "status",
    },
    UnsupportedEvent: {
        "dedupe_key",
        "raw_payload_sha256",
        "received_at",
        "occurred_at",
        "event_type",
    },
    WebhookEnvelope: {"events", "raw_body", "raw_payload_sha256", "received_at"},
}

EXPECTED_HANDWRITTEN_SIGNATURES = {
    MetaCloudClient: (
        "(*, access_token: 'str | SecretStr | AccessTokenProvider', "
        "phone_number_id: 'str', graph_version: 'str', "
        "http_client: 'httpx.AsyncClient | None' = None, "
        "base_url: 'str' = 'https://graph.facebook.com', "
        "timeout_seconds: 'float' = 15.0) -> 'None'"
    ),
    StaticAccessToken: "(token: 'str | SecretStr') -> 'None'",
    WebhookVerifier: "(*, app_secret: 'str | bytes', verify_token: 'str') -> 'None'",
    create_meta_webhook_router: (
        "(*, path: 'str' = '/integrations/whatsapp/meta', "
        "verifier: 'WebhookVerifier', event_sink: 'EventSink', "
        "max_body_bytes: 'int' = 1000000, max_events: 'int' = 1000, "
        "max_json_depth: 'int' = 64) -> 'APIRouter'"
    ),
    decode_envelope: (
        "(raw_body: 'bytes', *, received_at: 'datetime | None' = None, "
        "max_body_bytes: 'int' = 1000000, max_events: 'int' = 1000, "
        "max_json_depth: 'int' = 64) -> 'WebhookEnvelope'"
    ),
    payload_sha256: "(raw_body: 'bytes') -> 'str'",
    signature_for: "(raw_body: 'bytes', app_secret: 'str | bytes') -> 'str'",
    verify_challenge: "(received_token: 'str | None', expected_token: 'str') -> 'None'",
    verify_signature: (
        "(raw_body: 'bytes', signature_header: 'str | None', "
        "app_secret: 'str | bytes') -> 'None'"
    ),
    WhatsAppProvider.send: "(self, command: 'OutboundCommand') -> 'SendResult'",
}


def test_root_exports_are_frozen() -> None:
    assert outlabs_whatsapp.__version__ == "0.1.0a1"
    assert tuple(outlabs_whatsapp.__all__) == EXPECTED_ROOT_EXPORTS
    assert tuple(outlabs_whatsapp.meta.__all__) == (
        "AccessTokenProvider",
        "MetaCloudClient",
        "StaticAccessToken",
    )
    assert tuple(outlabs_whatsapp.fastapi.__all__) == ("create_meta_webhook_router",)
    assert tuple(outlabs_whatsapp.testing.__all__) == (
        "FakeEventSink",
        "FakeWhatsAppProvider",
        "build_status_webhook",
        "build_text_webhook",
        "encode_payload",
        "signed_headers",
    )


def test_public_model_field_names_and_order_are_frozen() -> None:
    for model, expected_fields in EXPECTED_MODEL_FIELDS.items():
        assert tuple(model.model_fields) == expected_fields
        assert {
            name for name, field in model.model_fields.items() if field.is_required()
        } == EXPECTED_REQUIRED_FIELDS[model]


def test_handwritten_call_signatures_are_frozen() -> None:
    for public_callable, expected_signature in EXPECTED_HANDWRITTEN_SIGNATURES.items():
        assert str(inspect.signature(public_callable)) == expected_signature
