# Consumer security checklist

- Store access/app/verification secrets in the application's secret store, not database rows.
- Rotate credentials through callable token providers.
- Use the default Meta HTTPS origin in production; review any custom HTTPS origin as a privileged
  egress configuration change.
- Resolve tenant/branch only from trusted signed WABA/phone-number mappings.
- Keep recipients, message bodies, template parameters, portal tokens, and webhook bodies out of
  logs, metrics, traces, TaskQ payloads, exceptions, snapshots, and support tickets.
- Persist a send intent before enqueueing; re-check current consent/suppression immediately before
  sending.
- Use a unique inbox constraint and monotonic status projection.
- Quarantine signed events for unknown phone-number IDs.
- Give raw webhook storage an encrypted tenant boundary and explicit TTL, or do not retain it.
- Test token rotation, replay, duplicates, reversed statuses, provider outage, kill switch, and
  offboarding before production.
- Keep the 95% branch-coverage, warnings-as-errors, Ruff security rules, dependency audit, and clean
  wheel smoke gates enabled in consumer CI.
- Treat phone possession and a WhatsApp click as insufficient identity proof.
