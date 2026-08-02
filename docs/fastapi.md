# FastAPI integration

Install the `fastapi` extra and mount a router returned by `create_meta_webhook_router`.

The adapter performs this order:

1. require uncompressed `application/json` and reject an invalid/oversized body;
2. read the exact raw bytes once;
3. validate `X-Hub-Signature-256` against the Meta app secret;
4. decode and normalize the payload;
5. hand a `WebhookEnvelope` to the application sink;
6. return 200 only after the sink returns `accepted` or `duplicate`.

The application sink owns persistence. In a TaskQ host it should insert/deduplicate the inbox row
and enqueue the application event task in one transaction before returning.

Use one endpoint-scoped `WebhookVerifier`. If multiple Meta apps are used during migration, give
each app a distinct route/verifier; do not parse an unsigned payload to choose an app secret.

The FastAPI adapter and standalone decoder both default to a 1 MB body limit. Callers may configure
up to the hard 16 MB ceiling, but should keep the limit as small as real Meta payloads permit.

Both entry points default to 1,000 normalized events per envelope and allow a configured range of
1–10,000. Exceeding the limit rejects the complete envelope rather than silently dropping events.
JSON nesting defaults to 64 levels and permits an explicit range of 1–256.

FastAPI access/error logging must not record query verification tokens, signature headers, bodies,
phone numbers, or validation payloads.
