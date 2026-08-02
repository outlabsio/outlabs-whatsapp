# 2026-08-02 Meta test-WABA send proof

## Scope and outcome

- Environment: unpublished Outlabs Automation development app, Meta-provided test WABA and test
  sender, and a maintainer-owned recipient already verified in Meta's test allowlist.
- Authorization: one corrected `hello_world` send was explicitly approved after the earlier
  recipient-format finding.
- Result: the guarded manual test completed successfully and asserted that Meta returned a
  `wamid.` acceptance identifier while preserving the package host reference.
- Meaning: this proves command serialization, authenticated transport, accepted-response parsing,
  and the corrected test-recipient configuration. The maintainer subsequently supplied a handset
  screenshot showing the `Hello World` message present in the recipient's WhatsApp conversation at
  10:29 AM, providing human-observed receipt evidence. It does not replace a signed provider
  `delivered` or `read` webhook.

No CdN applicant, QDarte user, production sender, portal link, customer content, or production
account was used.

## Execution evidence

- Graph version: `v25.0`.
- Template: Meta's neutral `hello_world` test template in `en_US`.
- Guarded invocation: `uv run pytest --no-cov -m manual
  tests/manual/test_meta_test_waba.py -q`.
- Result: 1 passed in 6.13 seconds.
- The first local wrapper invocation stopped during configuration validation because it used stale
  environment-variable aliases. It made no provider request. The corrected invocation made the one
  authorized provider call; no automatic provider retry occurred.
- The recipient value came verbatim from Meta's generated cURL example rather than being rebuilt
  from the maintainer's contact representation.
- The handset screenshot was reviewed in place but not copied into the repository because it shows
  the Meta test sender number. This review record retains only the sanitized observation.

## Credential handling

- The access token was limited to the current test WABA and moved from the authenticated browser
  session to the one test process through a one-use FIFO.
- No token, recipient, phone-number ID, returned `wamid`, raw provider response, or message content
  was placed in a command argument, repository file, `.env`, shell history, or review artifact.
- Immediately after the proof, the short-lived token's permissions were revoked. A follow-up Graph
  request rejected the token with HTTP 401 / provider code 190.

## Gates still open

Completed after this send proof: the clean installed-wheel CdN provider adapter,
the signed FastAPI sink backed by CdN Postgres and application-owned TaskQ,
duplicate/invalid-signature/unknown-sender-ID/privacy tests, monotonic delivery
state, TaskQ verification, and application migration rollback rehearsal.

1. Public HTTPS callback configured with a fresh app secret and verification token.
2. Live GET challenge plus signed inbound reply and sent/delivered/read callback evidence.
3. Release review before publishing an artifact or enabling any real application delivery.
