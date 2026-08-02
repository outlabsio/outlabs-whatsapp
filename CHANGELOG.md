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
