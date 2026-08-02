# 2026-08-02 Meta live webhook conformance proof

## Scope and outcome

- Package candidate: `outlabs-whatsapp` `0.1.0a1` from commit
  `47bf8d9db20eb9a4f7d105bfa05b04aea84bab63`, installed from a wheel with SHA-256
  `3921de38cb7ed29c012c6490e5517817afcc2cb6a716a570fbf06bd462863460`.
- Consumer boundary: Créditos del Norte API commit
  `f5f4602f1581ca335a31af76ccd07fbe33c99c34`, installed from its wheel into the same clean
  Python 3.13.9 environment.
- Provider environment: unpublished Outlabs Automation development app and Meta's dashboard-
  generated synthetic `messages` sample at Graph version `v26.0`.
- Result: the exact package candidate passed the public challenge, signed-event, durable quarantine,
  replay-deduplication, and invalid-signature checks through the real consumer FastAPI/Postgres
  boundary.

No CdN applicant, QDarte user, production sender, portal link, customer content, or production
account was used.

## Live evidence

1. Meta verified and saved a fresh public HTTPS callback using a random one-use verification token.
   A separate public GET challenge returned HTTP 200 and echoed only the exact challenge.
2. The app's WhatsApp Business Account `messages` field was subscribed at `v26.0`.
3. Meta's dashboard sent its signed synthetic incoming-text sample to the public callback. Meta
   reported a successful field test and the consumer persisted exactly one `inbound_text` inbox
   record.
4. The dashboard sample intentionally contains Meta placeholder metadata rather than the configured
   test sender identifier. The consumer therefore closed the record as `needs_review` with
   `phone_number_id_not_allowlisted`, without enqueuing host work. This is the expected fail-closed
   behavior for an unknown sender identifier.
5. The durable record retained a 64-character deduplication key and a 64-character raw-payload
   SHA-256 digest. It did not retain the raw webhook body.
6. Sending the identical Meta sample a second time again produced a provider success indication,
   while the inbox remained at one row, one deduplication key, and one payload digest.
7. A public POST with an invalid `X-Hub-Signature-256` value returned HTTP 401 and created no inbox
   record.

## What this proves

The proof covers public HTTPS routing, exact-token challenge verification, Meta app-secret HMAC
verification over the raw body, the installed package's FastAPI adapter, the application-owned
durable sink, unknown-identifier quarantine, privacy-minimal persistence, and idempotent replay
handling. It also confirms that the package and consumer wheel used for the proof were the reviewed
release candidates rather than editable checkouts.

The app was unpublished, so Meta permits dashboard-generated test webhooks but not real production
traffic. This proof therefore does not claim a real customer inbound message or live
`sent`/`delivered`/`read` transition. Those shapes and monotonic transitions remain covered by the
installed-artifact consumer contracts; a real staging-number callback remains an activation gate
before production delivery.

## Credential and data handling

- The existing app secret moved from the authenticated Meta session directly into the one proof
  process through a one-use FIFO. The random verification token and allowlisted test sender
  identifier used the same memory/FIFO-only path.
- No secret, token, callback hostname, signature, phone number, WABA identifier, phone-number
  identifier, provider message identifier, raw webhook body, or message content was written to the
  repository, shell history, review record, or application database.
- No access token or provider send was needed for the callback proof. The short-lived access token
  used by the earlier test-WABA send had already been revoked and independently shown to fail with
  HTTP 401 / provider code 190.

## Verified teardown

- Meta's callback URL and verification-token fields were emptied and the `messages` field returned
  to `Unsubscribed`.
- The disposable public tunnel and exact-candidate FastAPI server were stopped; the local proof port
  no longer had a listener.
- The disposable Postgres container was stopped and removed.
- The private temporary tree, including both secret FIFOs, proof wheels, virtual environment, and
  callback script, was deleted.
- App-secret, verification-token, provider-identifier, callback-URL, and raw-browser-snapshot values
  were cleared from the browser-control runtime.

