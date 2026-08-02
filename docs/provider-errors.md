# Provider errors

The direct Meta adapter classifies failures conservatively:

| Error | Default host disposition |
| --- | --- |
| `RateLimitedError` | bounded retry using the safe provider hint |
| `ProviderUnavailableError` | bounded retry when the request is known not to have sent |
| `AuthenticationError` | terminal/configuration alert |
| `PolicyError` | terminal/policy review |
| `InvalidRecipientError` | terminal/contact remediation |
| `InvalidTemplateError` | terminal/template remediation |
| `InvalidRequestError` | terminal/developer/configuration review |
| `AmbiguousSendError` | `needs_review`; never automatic resend |
| `MalformedProviderResponseError` | terminal/reconciliation review |

Meta error codes evolve. Unknown 4xx responses are terminal invalid requests. Generic 5xx responses
are ambiguous because an HTTP response alone does not prove the send was rejected before provider
acceptance. Only pre-send connection establishment failures are provider-unavailable by default.
Update code mappings only with official documentation and contract tests.
