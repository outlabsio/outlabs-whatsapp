# Release process

Releases are immutable GitHub tags and attached wheel/source artifacts. A consumer must pin the
exact artifact URL and SHA-256 digest; a mutable branch, local path, or editable install is never a
release dependency.

## Alpha release gate

Before creating a tag:

1. complete the synthetic Meta test-WABA send and live signed-callback conformance proofs;
2. retain only sanitized evidence—never credentials, numbers, raw webhook bodies, message content,
   WABA identifiers, phone-number identifiers, or template parameters;
3. scan the complete reachable Git history for credentials and private recipient/provider data;
4. run Ruff, strict mypy, pytest with the coverage gate, and the dependency audit on both supported
   Python versions;
5. build the wheel and source archive twice and prove each pair is byte-identical;
6. install the wheel outside the checkout and run the installed-artifact contract;
7. push the exact candidate commit and require the hosted `ci` workflow to pass; and
8. create the signed-off release tag only from that green commit.

The tag-triggered hosted workflow repeats the full Python 3.12/3.13 matrix. Publish the GitHub
release only after that run succeeds.

## Release evidence

Each release record must include:

- version, tag, and full commit SHA;
- hosted CI run URL for the tag;
- SHA-256 digests for the wheel and source archive;
- local validation counts and supported Python versions;
- the sanitized Meta conformance evidence references;
- the history/privacy audit result; and
- the first consumer's immutable URL/digest pin and clean-wheel contract result.

The release body must link to the corresponding record under `docs/review/`. If an artifact or tag
is wrong, publish a new version; do not replace attached files or move the existing tag.

## Consumer handoff

Consumers keep persistence, consent, suppression, template policy, TaskQ registration, retry,
reconciliation, and credential ownership. Installing a release does not authorize production data
or delivery. Each consumer must preserve its own synthetic, staging, and production gates.
