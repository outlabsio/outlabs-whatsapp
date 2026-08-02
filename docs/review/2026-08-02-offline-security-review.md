# 2026-08-02 offline security and contract review

- Scope: local `0.1.0a1` after initial baseline commit `21872c8`
- Perspectives: package maintainer, CdN consumer, hostile/provider-controlled input
- Production data/credentials: none
- Result: offline gate passes after the resolved findings below

## Resolved findings

| ID | Severity | Finding | Resolution and evidence |
| --- | --- | --- | --- |
| F-01 | high | An injected `httpx.AsyncClient` could use a cleartext base URL despite the documented HTTPS guarantee. | Validate the injected client's origin, send to a captured absolute HTTPS origin, reject conflicting `base_url`, and test the bypass. |
| F-02 | high | Transport, malformed-JSON, and host-sink exception chains could expose upstream text in formatted tracebacks. | Suppress raw causes, replace sink exceptions with a safe package error, and assert sentinel text is absent from formatted tracebacks. |
| F-03 | medium | `str.isdigit()` accepted non-ASCII Unicode digits as recipients. | Require 7–20 ASCII decimal digits and add a Unicode-digit rejection contract. |
| F-04 | medium | A non-error redirect carrying a message-shaped JSON body could be treated as accepted. | Disable redirects per request and require an actual 2xx response; test with an injected client configured to follow redirects. |
| F-05 | medium | Valid JSON could consume unbounded normalization work within the body cap. | Default to 1 MB, depth 64, and 1,000 normalized events; expose bounded tuning; reject the whole envelope rather than partially acknowledge it. |
| F-06 | medium | Oversized/non-ASCII provider message and trace identifiers could escape the closed response contract. | Validate message IDs as bounded visible ASCII and discard unsafe trace identifiers. |
| F-07 | medium | Public free verification helpers accepted empty secrets/tokens even though `WebhookVerifier` rejected them. | Apply the same configuration validation to every public verification entry point. |
| F-08 | medium | A host sink exception could expose application text through the ASGI exception path. | Convert ordinary sink exceptions to `RuntimeError("event sink failed")` with suppressed context; preserve cancellation. |
| F-09 | low | Streaming code copied an over-limit chunk before rejecting it. | Check remaining capacity before extending the body buffer. |
| F-10 | low | Concurrent/closed lifecycle calls had under-specified behavior. | Mark owned clients closed before awaiting close, reject re-entry, preserve cancellation, and test concurrent token resolution/sends. |
| F-11 | medium | `httpx.URL` accepted malformed bracketed-host input, leaving the origin contract dependent on permissive parser behavior. | Pre-validate bounded visible-ASCII origins with `urllib.parse`, reject malformed ports, brackets, controls, and backslashes, then apply the existing `httpx` origin checks. |

## Maintainer review

- Root exports, submodule exports, model field order/requiredness, and handwritten signatures have an
  executable snapshot.
- Five accepted ADRs define package ownership, retry, event versioning, webhook acknowledgement,
  and observability.
- Current and declared-minimum runtime dependencies pass on Python 3.12/3.13.
- Independently built wheel/sdist pairs are byte-identical; the isolated installed wheel executes
  a real command-to-mocked-Meta send and a signed FastAPI webhook round trip.

## CdN consumer review

- No CdN tenant, consent, template, secure-link, persistence, or TaskQ behavior entered the package.
- Queue composition remains intent-ID-only and application-owned.
- Ambiguous sends remain terminal for automatic resend and require host review/reconciliation.
- CdN now has an application-owned durable outbox, metadata-only inbox, explicit WhatsApp consent,
  production-forbidden fake provider, and worker-callable dispatch boundary on its isolated consumer
  branch. Its 107-test suite and Alembic downgrade/upgrade/drift checks pass without adding a path,
  provider-package, or TaskQ dependency.

## Hostile-input review

- Exact HMAC verification still precedes JSON parsing and parsed-identifier trust.
- Non-JSON media, compression, malformed/constant/deep JSON, body limits, event limits, invalid
  signatures, redirects, unsafe identifiers, header-injection tokens, and sink failures fail closed.
- Property tests continue generating arbitrary JSON objects and body/signature mutations.
- The package emits no default log records and leak sentinels are absent from safe exception output.

## Open residual risks and gates

1. Live Meta request, response, challenge, signature, and callback shapes are not yet proven. Use a
   synthetic test WABA only and promote sanitized observations into fixtures.
2. The fake CdN persistence/dispatch path is proven, but the concrete installed-package adapter,
   signed FastAPI webhook sink, application worker registration, and external crash-window
   reconciliation remain gated.
3. A host-provided token callback or HTTP client can contain its own logging/hooks and remains host
   code outside the package's containment boundary.
4. Meta send delivery cannot be exactly-once across the acceptance/persistence crash window.
5. Signed raw bodies necessarily exist in process memory; retention and process diagnostics remain
   host-controlled.

The package is ready for the next gated activity—synthetic live conformance prerequisite audit—but
is not approved for publication, production data, or a production number.
