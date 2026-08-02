# Public contracts

## Core import

`import outlabs_whatsapp` imports only the core dependencies (`pydantic` and `httpx`). It must not
import FastAPI, SQLAlchemy, outlabs-auth, or taskq.

## Commands

Commands are frozen Pydantic models. Recipients, message bodies, button values, and template
parameters are excluded from their representations. Serialization still includes them because the
Meta adapter must send them; consumers must not log `model_dump()` output.

Pydantic validation errors hide input values. This does not make serialized models safe to log.

The v0.1 command variants are:

- `TextCommand`;
- `TemplateCommand` with typed body and button components;
- `InteractiveButtonsCommand` with one to three reply buttons.

## Provider result

`SendResult` means Meta accepted the request and returned a message ID. It does not mean the message
was delivered. Delivery/read/failure state arrives through webhooks.

## Errors

Provider exceptions contain safe category, integer code/subcode, HTTP status, and optional provider
trace ID only. Meta's raw error message/details are not retained because they may echo request data.

An `AmbiguousSendError` means the request may have reached Meta. It must not be retried blindly.

Only 2xx responses can produce `SendResult`; redirects are never followed by the provider request.
Provider message IDs must be bounded visible ASCII. Unsafe provider trace identifiers are discarded.

## Events

Normalized webhook events carry schema version `1`, a deterministic dedupe key, provider IDs,
provider/receive timestamps, and a hash of the signed raw payload. Message content and recipient
identifiers are excluded from representations but remain sensitive values in memory.

All normalized timestamps are timezone-aware. Oversized or malformed provider fields become an
`UnsupportedEvent` rather than escaping the normalizer as a validation failure.

Unknown signed event types become `UnsupportedEvent`; they are never silently mapped to a default
tenant.
