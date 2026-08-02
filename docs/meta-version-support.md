# Meta Graph API version support

The Graph API version is required configuration and is never silently selected by the package.

Before changing the production version:

1. confirm the version and migration notes in Meta's official documentation;
2. update the sanitized request/webhook fixtures;
3. run source, wheel, and consumer contract suites;
4. run the disabled/manual Meta test-WABA smoke;
5. deploy to a non-production consumer environment before production.

Package version, normalized event schema version, and Meta Graph API version are independent.

The [manual test-WABA smoke](manual-meta-smoke.md) requires an explicit version and never chooses or
updates a Meta Graph version automatically.
