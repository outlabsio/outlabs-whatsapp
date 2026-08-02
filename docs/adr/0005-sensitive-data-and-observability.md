# ADR 0005: sensitive data and observability

- Status: accepted
- Date: 2026-08-02

## Context

Recipients, content, template values, portal links, credentials, and webhook bodies can leak through
representations, validation failures, provider errors, queue payloads, logs, traces, and fixtures.

## Decision

Sensitive command/event/envelope fields are excluded from model representations. Pydantic input
values are hidden in validation errors. Credentials use redacted containers and header-safe
validation. Provider errors discard upstream text and bodies.

The package provides fingerprints and masked suffixes for bounded diagnosis, but it does not log.
Consumers may use provider IDs, closed enums, safe integer codes, and non-reversible fingerprints as
operational fields. They must not record model dumps, raw bodies, recipients, content, template
parameters, secrets, portal values, or user-controlled text.

Synthetic fixtures use reserved/fake values. Secret scanning and explicit capture tests are release
gates. Raw webhook retention, if any, is encrypted, tenant-scoped, access-controlled, and TTL-bound
by the host.

## Consequences

- Debugging favors safe identifiers over complete payload inspection.
- Serialization remains sensitive even when `repr` is safe.
- A new public field requires an explicit sensitivity classification and leak test.
