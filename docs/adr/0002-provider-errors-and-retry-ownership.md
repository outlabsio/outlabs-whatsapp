# ADR 0002: provider errors and retry ownership

- Status: accepted
- Date: 2026-08-02

## Context

An HTTP failure does not always reveal whether Meta received a send. A generic retry can therefore
duplicate an external message. Raw Meta errors may also echo sensitive request data.

## Decision

The provider exposes closed, safe error categories. It never performs an internal durable retry.
Known pre-send connection failures become `ProviderUnavailableError`; read/write/remote-protocol
and otherwise uncertain transport failures become `AmbiguousSendError`.

Provider error strings retain only category, integer code/subcode, HTTP status, and an optional
trace identifier. Raw provider messages, response bodies, recipients, and command content are not
retained. Unknown 4xx responses are terminal invalid requests; unknown 5xx responses are provider
unavailability.

The host owns retry budget, persistence, reconciliation, and operator escalation. It must never
automatically resend an ambiguous outcome.

## Consequences

- Some uncertain sends require manual review rather than automatic recovery.
- Adding or remapping a provider code requires official evidence and contract tests.
- The package cannot claim exactly-once external delivery.
