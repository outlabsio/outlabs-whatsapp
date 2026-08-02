# Threat model

This model covers the reusable package boundary. It does not replace a consumer-specific threat
model for CdN, QDarte, or another tenant/application.

## Assets and trust boundaries

Sensitive assets are Meta access/app/verification secrets, recipients, message and template
content, portal links/tokens, signed webhook bodies, and tenant routing identifiers.

The package crosses three boundaries:

1. host application to the command/provider API;
2. provider client to Meta over HTTPS;
3. public Meta webhook endpoint to the application-owned durable event sink.

Meta is trusted to authenticate its signed payloads, but every payload remains untrusted data. A
valid signature does not establish the tenant unless the host maps the signed WABA/phone-number ID
through its own trusted configuration.

## Package-controlled threats

| Threat | Package control |
| --- | --- |
| Secret/content leakage in normal logging | sensitive fields excluded from representations and validation errors; provider messages discarded |
| Access-token header injection | non-empty visible-ASCII credential validation |
| Cleartext or credential-bearing provider origin | HTTPS origin-only validation with no user info, path, query, or fragment |
| Forged webhook | exact HMAC-SHA256 verification over raw bytes before JSON decoding |
| Body/decompression abuse | uncompressed JSON requirement plus streaming and decoder size caps |
| Schema drift or oversized provider fields | tolerant, bounded normalization to versioned events or `UnsupportedEvent` |
| Duplicate provider callbacks | deterministic dedupe key contract; durable uniqueness remains host-owned |
| Unsafe automatic retry after uncertain transport failure | explicit `AmbiguousSendError` category |
| Dependency/CI regression | locked dependencies, audit, pinned actions, read-only CI token, warnings-as-errors, 95% branch coverage, clean-wheel smoke |

## Host-controlled threats

The consuming service must enforce consent and suppression, message purpose, expiring opaque links,
tenant isolation, authorization, rate limits, durable outbox/inbox transactions, replay handling,
monotonic delivery-state projection, encrypted retention/TTL, kill switches, and audited credential
rotation. It must never place content, recipients, or secrets in queue payloads, logs, traces, error
reporting, or support tickets.

An application compromise, a leaked Meta credential, malicious application-provided token callback,
or incorrect tenant mapping is outside the package's ability to contain and requires host-level
incident controls.

## Release evidence

Before release, pass Ruff including security rules, strict mypy, the adversarial/property suite on
Python 3.12 and 3.13, dependency audit, source/wheel builds, and clean installed-wheel imports. A
real Meta test-WABA smoke remains a manual release gate and must use synthetic data only.
