# ADR 0004: webhook verification and acknowledgement

- Status: accepted
- Date: 2026-08-02

## Context

Webhook routes are public ingress. Parsed identifiers cannot be trusted before signature
verification, and returning success before durable acceptance can lose events permanently.

## Decision

The adapter verifies the exact lowercase `sha256=<64 hex>` HMAC over the unmodified body before JSON
decoding or tenant routing. Endpoint-scoped verifiers avoid parsing unsigned data to select a
secret. The FastAPI adapter accepts only uncompressed `application/json`, streams to a configured
limit, and normalizes only after verification.

The route also enforces the configured normalized-event cap. A body that exceeds either bound is
rejected; events are never partially acknowledged. JSON nesting defaults to a maximum depth of 64
and may be configured from 1 through 256.

The router returns 200 only after the host sink returns `accepted` or `duplicate`. Sink exceptions
and invalid acceptances fail closed with 5xx so Meta can retry. The host sink must durably insert or
deduplicate and enqueue application work before returning.

## Consequences

- Slow durable sinks consume webhook response time and must be operationally bounded by the host.
- Multiple Meta apps use distinct routes/verifiers during migration.
- Access logging must redact verification query tokens, signatures, and bodies.
