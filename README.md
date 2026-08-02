# outlabs-whatsapp

Typed, framework-light WhatsApp Business Platform integration for Python services.

**Status:** pre-alpha. The repository is currently local and unpublished. The intended licence is
MIT and the intended public home is `outlabsio/outlabs-whatsapp` after the first release gate.

The library knows how Meta WhatsApp works. The consuming application decides whether, why, when,
and to whom a message may be sent.

## Boundaries

The package provides:

- typed text, template, and reply-button commands;
- a direct async Meta Cloud API client;
- safe provider error categories, including ambiguous-send handling;
- raw-body webhook signature/challenge verification;
- versioned normalized inbound/status events;
- an optional signature-first FastAPI router;
- no-network provider and webhook test fakes.

See the package [threat model](docs/threat-model.md) for the trust boundaries and the controls the
host application must still provide.

The package does not provide a database, queue, worker, campaign system, consent policy, tenant
model, templates, AI agent, or inbox UI. See [contracts](docs/contracts.md).

The accepted v0.1 boundaries and change-control rules are recorded in the
[architecture decisions](docs/adr/README.md).
The latest completed gate is the
[offline security and contract review](docs/review/2026-08-02-offline-security-review.md).

## Install for development

```bash
uv sync --extra fastapi --group dev
```

## Send through Meta

```python
import os

from outlabs_whatsapp import MetaCloudClient, TemplateCommand

async with MetaCloudClient(
    access_token=lambda: os.environ["META_WHATSAPP_ACCESS_TOKEN"],
    phone_number_id=os.environ["META_WHATSAPP_PHONE_NUMBER_ID"],
    graph_version=os.environ["META_GRAPH_VERSION"],
) as client:
    result = await client.send(
        TemplateCommand(
            to="+15550001111",
            name="application_update_available",
            language_code="es_AR",
            host_reference="send-intent-id",
        )
    )
```

The application must complete its consent, suppression, purpose, link-expiry, tenant, and kill-
switch checks immediately before calling `send`. Never invoke the provider directly from a request
transaction or an in-process FastAPI background task.

## FastAPI webhook

```python
import os

from fastapi import FastAPI
from outlabs_whatsapp.fastapi import create_meta_webhook_router
from outlabs_whatsapp.webhooks import WebhookVerifier

app = FastAPI()
app.include_router(
    create_meta_webhook_router(
        verifier=WebhookVerifier(
            app_secret=os.environ["META_APP_SECRET"],
            verify_token=os.environ["META_WEBHOOK_VERIFY_TOKEN"],
        ),
        event_sink=application_durable_event_sink,
    )
)
```

The sink must durably insert/deduplicate the event and enqueue application-owned processing before
returning. See [FastAPI integration](docs/fastapi.md).

## TaskQ

There is deliberately no `outlabs-whatsapp[taskq]` extra. Register an application-owned TaskQ job
whose payload contains only a `send_intent_id`, then call `MetaCloudClient` inside that handler. See
the [TaskQ consumer recipe](docs/taskq-consumer.md).

## Validation

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv run --with pip-audit pip-audit --skip-editable
uv build
```

`pytest` enforces branch coverage at 95% and treats warnings as failures. CI runs the complete gate
on Python 3.12 and 3.13, then installs the built wheel into a clean environment for an import smoke.

The real [Meta test-WABA smoke](docs/manual-meta-smoke.md) is double-guarded, synthetic-only, and
excluded from normal CI.

See the [release process](docs/release.md) for the immutable tag, artifact, evidence, and consumer
pinning gates.
