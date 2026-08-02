# 2026-08-02 Meta test-WABA send proof

## Scope and outcome

- Environment: unpublished Outlabs Automation development app, Meta-provided test WABA and test
  sender, and a maintainer-owned recipient already verified in Meta's test allowlist.
- Authorization: one corrected `hello_world` send was explicitly approved after the earlier
  recipient-format finding.
- Result: the guarded manual test completed successfully and asserted that Meta returned a
  `wamid.` acceptance identifier while preserving the package host reference.
- Meaning: this proves command serialization, authenticated transport, accepted-response parsing,
  and the corrected test-recipient configuration. Provider acceptance is not proof of delivery or
  reading.

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

## Credential handling

- The access token was limited to the current test WABA and moved from the authenticated browser
  session to the one test process through a one-use FIFO.
- No token, recipient, phone-number ID, returned `wamid`, raw provider response, or message content
  was placed in a command argument, repository file, `.env`, shell history, or review artifact.
- Immediately after the proof, the short-lived token's permissions were revoked. A follow-up Graph
  request rejected the token with HTTP 401 / provider code 190.

## Gates still open

1. Public HTTPS callback configured with a fresh app secret and verification token.
2. Live GET challenge plus signed inbound reply and sent/delivered/read callback evidence.
3. Live duplicate, invalid-signature, and unknown phone-number-ID handling through an
   application-owned durable synthetic sink.
4. A concrete installed-package CdN adapter and reconciliation proof.
5. Release review before publishing an artifact or enabling any real application delivery.

