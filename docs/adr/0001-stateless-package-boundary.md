# ADR 0001: stateless package boundary

- Status: accepted
- Date: 2026-08-02

## Context

CdN and QDarte need the same Meta transport, webhook verification, normalized events, and testing
mechanics. Their consent, tenant, workflow, persistence, and operational rules are different.

## Decision

`outlabs-whatsapp` is a stateless, framework-light library. It owns typed provider mechanics and an
optional FastAPI adapter. It does not own a database, migrations, queue, worker, tenant registry,
consent, suppression, templates, campaigns, secure links, AI, inbox UI, or hosted gateway.

TaskQ remains application-owned. Queue payloads carry an application intent identifier only; the
host reloads current authoritative state immediately before constructing a command and sending.

Core imports remain independent of FastAPI, SQLAlchemy, outlabs-auth, and TaskQ.

## Consequences

- Consumers duplicate small amounts of application wiring.
- No package callback system is introduced to simulate application persistence or policy.
- Shared glue is reconsidered only after both consumers produce identical, policy-free code.
- Adding a prohibited responsibility requires a superseding ADR and a new product-boundary review.
