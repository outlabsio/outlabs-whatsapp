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

Meta error codes evolve. Unknown 4xx responses are terminal invalid requests; unknown 5xx responses
are provider-unavailable. Update code mappings only with official documentation and contract tests.
