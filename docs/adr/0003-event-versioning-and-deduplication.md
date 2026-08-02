# ADR 0003: normalized event versioning and deduplication

- Status: accepted
- Date: 2026-08-02

## Context

Meta webhooks are at-least-once, can arrive out of order, and evolve independently of package and
consumer releases. Applications need a stable contract without treating a webhook as projected
business state.

## Decision

Normalized events are immutable, timezone-aware, discriminated models with `schema_version="1"`, a
hash of the signed raw payload, and a deterministic dedupe key. Provider status callbacks remain
individual facts in received order; the package does not project monotonic delivery state.

Message dedupe keys derive from the provider message ID and event type. Status dedupe keys also
include status and provider timestamp. Events without stable provider identifiers use bounded safe
metadata plus the raw-payload hash. Unknown, malformed, or oversized signed fields degrade to
`UnsupportedEvent` when the envelope itself remains valid.

Decoding defaults to at most 1,000 normalized events per envelope and permits explicit host tuning
from 1 through 10,000. Exceeding the cap rejects the envelope instead of silently dropping events.

Existing schema-v1 fields and meanings are not changed in place. A breaking normalized-event change
introduces a new schema version and migration/conformance fixtures.

## Consequences

- Durable uniqueness and monotonic projection remain consumer responsibilities.
- Raw-payload hashes support diagnosis without making raw-body retention mandatory.
- Future Meta fields do not silently acquire tenant or business meaning.
