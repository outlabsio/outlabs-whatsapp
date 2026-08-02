# Security policy

`outlabs-whatsapp` is pre-alpha. Only the latest tagged alpha is supported.

Report vulnerabilities privately to `contact@outlabs.io`. Do not include live access tokens,
app secrets, verification tokens, phone numbers, message contents, webhook bodies, WABA IDs, or
customer data in a public issue.

The library treats credentials and message contents as sensitive. Consumers are responsible for
their own consent, data retention, tenant isolation, persistence, queue, and authorization rules.

Direct Meta transport requires an HTTPS origin. Access tokens must be visible ASCII so they cannot
inject HTTP headers. Webhooks require exact HMAC-SHA256 verification before JSON decoding, reject
compressed/non-JSON requests in the FastAPI adapter, and enforce bounded bodies.

See [the threat model](docs/threat-model.md) and the
[consumer security checklist](docs/consumer-security-checklist.md).
