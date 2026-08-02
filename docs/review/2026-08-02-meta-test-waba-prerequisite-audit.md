# 2026-08-02 Meta test-WABA prerequisite audit

## Scope and outcome

- Environment: unpublished Outlabs Automation development app, Meta-provided test WABA and test
  sender, maintainer-owned synthetic recipient only.
- No CdN applicant, QDarte user, production number, portal link, customer content, or production
  account was used.
- Result: recipient and credential prerequisites pass; the first guarded `hello_world` request was
  rejected before acceptance with provider code `131030`, so no message ID or delivery was created.
  A corrected retry remains human-gated.

## Security evidence

- The recipient completed Meta's WhatsApp OTP flow and appears in the test sender's recipient list.
- The generated user token was limited to the current test WABA instead of all current and future
  WhatsApp accounts.
- A token exposed during diagnostic output was treated as compromised immediately. Its permissions
  were revoked successfully, and a follow-up Graph request proved rejection with HTTP 401 / provider
  code 190. A clean replacement was then generated and retained in memory only.
- No token, recipient, OTP, message body, raw provider response, or webhook body was written to the
  repository, an `.env`, or review evidence.

## Request evidence and finding

- The double opt-in guards allowed exactly one manual test invocation through `MetaCloudClient`.
- Meta returned HTTP 400 / provider code `131030`; the library raised a terminal error and did not
  retry.
- The provider-generated `to` value in Meta's test-page cURL did not equal the maintainer contact's
  canonical E.164 digits. The smoke configuration must use Meta's exact verified/allowlisted `to`
  value, especially for national numbering plans with provider-specific rendering.
- The corrected value is staged but must not be retried without a new explicit send confirmation.

## Hardening produced by the audit

- Provider code `131030` is now classified as `InvalidRecipientError`.
- The manual smoke command disables whole-suite coverage for the intentionally isolated one-test
  invocation; the full suite continues to enforce the 95% gate.
- The runbook now requires copying the recipient from Meta's generated cURL and forbids automatic
  retries after an allowlist mismatch.

## Verification

- Full suite: 138 passed, 1 manual test skipped; 97.18% total coverage.
- Ruff: passes.
- Focused signed-callback contract proof: 8 passed, covering exact GET challenge token, valid
  signature before durable sink, invalid signature rejection, status normalization, stable dedupe
  key, and duplicate acceptance.

## Gates still open

1. Explicitly approved corrected `hello_world` send returning a redacted/fingerprinted `wamid`.
2. Public HTTPS callback configured with a fresh app secret and verification token.
3. Live GET challenge plus signed inbound reply and sent/delivered/read callback evidence.
4. Live duplicate, invalid-signature, and unknown phone-number-ID handling through the
   application-owned durable synthetic sink.
5. Concrete installed-package consumer adapter and reconciliation proof before any production
   enablement or public release.
