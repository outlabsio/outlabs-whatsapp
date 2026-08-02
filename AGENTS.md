# outlabs-whatsapp agent guide

This repository owns stateless WhatsApp Business Platform mechanics only.

## Hard boundaries

1. Core `import outlabs_whatsapp` must not import FastAPI, SQLAlchemy, outlabs-auth, or taskq.
2. Do not add a database, migrations, queue, worker supervisor, business templates, consent rules,
   campaigns, conversation memory, AI, or tenant configuration.
3. Never expose access tokens, app secrets, verification tokens, phone numbers, message bodies, or
   template parameters in representations, errors, logs, metrics, traces, fixtures, or snapshots.
4. Verify the raw webhook signature before trusting parsed identifiers.
5. Do not automatically retry ambiguous sends. The consuming application owns durable retry and
   reconciliation decisions.
6. Add or change a public contract only with tests, documentation, and changelog coverage.

## Validation

Run:

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv run --with pip-audit pip-audit --skip-editable
uv build
```

`pytest` must retain the warnings-as-errors and 95% branch-coverage gates. Run the full suite on
Python 3.12 and 3.13 before changing a public contract or release artifact.
