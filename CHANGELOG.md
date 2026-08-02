# Changelog

All notable changes to this project will be documented here.

## 0.1.0a1 — unreleased

- Establish the framework-light core contracts.
- Add the direct Meta Cloud API client.
- Add signature-first webhook verification and normalization.
- Add the optional FastAPI router and no-network testing helpers.
- Require HTTPS provider origins and reject header-unsafe access tokens.
- Bound webhook decoding and normalize oversized/future fields without leaking raw payloads.
- Hide sensitive values from Pydantic validation errors as well as model representations.
- Add adversarial/property tests and a 95% branch-coverage gate across Python 3.12 and 3.13.
- Pin CI actions by commit, minimize workflow permissions, and add dependency update automation.
- Accept the v0.1 boundary, retry, event, webhook, and sensitive-data ADRs.
- Freeze root exports, public model fields, and handwritten call signatures in contract tests.
- Add functional installed-wheel, minimum-runtime, and reproducible-artifact CI gates.
- Suppress sensitive upstream/sink exception chains and enforce a no-default-logging contract.
- Bound JSON nesting and normalized event counts without partial acknowledgement.
- Require injected clients to use HTTPS, disable redirects, and validate provider identifiers.
- Reject malformed ports, bracketed hosts, controls, and backslash-ambiguous provider origins.
- Reject Unicode-digit recipients and empty public verifier configuration.
- Record the three-perspective offline security/contract review and residual gates.
- Add a double-guarded, synthetic-only manual Meta test-WABA send gate and callback checklist.
