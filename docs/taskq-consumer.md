# TaskQ consumer recipe

TaskQ belongs in the application. `outlabs-whatsapp` has no TaskQ dependency or packaged worker.

## Payload

Queue an application identifier only:

```python
from uuid import UUID
from pydantic import BaseModel

class SendWhatsAppIntent(BaseModel):
    intent_id: UUID
```

Do not queue recipient numbers, message bodies, template parameters, portal tokens, WABA secrets,
or access tokens.

## Handler outline

```python
async def send_whatsapp(context, payload):
    intent = await repository.lock_intent(payload.intent_id)
    if intent.provider_message_id:
        return Complete(result={"status": "already_accepted"})

    decision = await policy.recheck(intent)
    if not decision.allowed:
        await repository.mark_skipped(intent, decision.safe_reason)
        return Complete(result={"status": "skipped"})

    command = application_command_factory(intent)
    try:
        result = await meta_client.send(command)
    except RateLimitedError as exc:
        return Retry(after_seconds=exc.retry_after_seconds, error="provider_rate_limited")
    except ProviderUnavailableError:
        return Retry(error="provider_unavailable")
    except AmbiguousSendError:
        await repository.mark_needs_review(intent, "ambiguous_send")
        return NonRetryable(error="ambiguous_send")
    except (AuthenticationError, PolicyError, InvalidRecipientError, InvalidTemplateError):
        await repository.mark_terminal_failure(intent, "provider_rejected")
        return NonRetryable(error="provider_rejected")

    await repository.mark_accepted(intent, result.message_id)
    return Complete(result={"status": "accepted", "message_id": result.message_id})
```

The real handler must use application-owned transactions and cancellation checks. Result/error
payloads must remain PII-free.

There is an unavoidable crash window between Meta accepting a send and persisting its message ID.
TaskQ does not make an external provider exactly-once. Treat uncertain outcomes conservatively and
never turn them into blind retries.

## Inbound

The FastAPI sink inserts/deduplicates the signed webhook inbox row and enqueues the application
`*.whatsapp.process_event` task in one transaction. The task payload carries the inbox row ID only.
