# Manual Meta test-WABA smoke

This gate performs a real external send. It is disabled by default and is never part of CI. Use
only Meta test assets, a synthetic/maintainer-owned recipient, and neutral `hello_world` content.
Do not use a CdN applicant, QDarte user, production number, portal link, or customer data.

## Prerequisites

Verify against Meta's current official WhatsApp Cloud API documentation/collection before every
run:

- Meta developer app and test WABA/test phone-number ID;
- explicit currently supported Graph API version;
- short-lived test access token with `whatsapp_business_messaging`;
- test recipient enabled for the app's test number;
- app secret and a randomly generated webhook verification token for callback testing;
- public HTTPS callback route, subscribed app/WABA, and a host sink that records only synthetic
  evidence.

The package smoke does not create/register a phone, subscribe an app, change a WABA, or configure a
callback. Those are explicit Meta console/API operations and must be reviewed separately.

## Send-only environment

Set these in a temporary secret-bearing shell/session, never in a committed `.env`:

```text
META_WHATSAPP_ACCESS_TOKEN
META_WHATSAPP_PHONE_NUMBER_ID
META_GRAPH_VERSION
META_TEST_RECIPIENT
META_SMOKE_ASSERT_SYNTHETIC=YES
OUTLABS_WHATSAPP_RUN_META_SMOKE=I_UNDERSTAND_THIS_SENDS_A_WHATSAPP_MESSAGE
```

Run only the manual test:

```bash
uv run pytest -m manual tests/manual/test_meta_test_waba.py
```

## Callback proof

After the neutral send succeeds, use the configured public HTTPS test route to prove:

1. GET challenge with the exact verification token;
2. signed inbound reply accepted only after the durable synthetic sink;
3. sent/delivered/read status normalization for the returned `wamid`;
4. duplicate callback acceptance without duplicate host work;
5. invalid signature and unknown phone-number ID rejection/quarantine;
6. token rotation followed by another neutral send.

Record only package version, Graph version, timestamps, closed event kinds/statuses, safe provider
codes, payload hashes, and redacted/fingerprinted IDs. Promote sanitized shapes into fixtures; never
store tokens, recipients, message content, signatures, or raw bodies in review evidence.
