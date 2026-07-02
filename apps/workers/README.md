# Workers — Python Background Workers

Background workers for scheduled detection, event processing, and eventually LLM/pipeline work.

## Stack
- Python 3.12+
- Supabase service-role client for server-side runtime work
- `python-dotenv` for local `.env` loading
- Shared API services imported from `apps/api`

## Implemented worker

### Stale quote worker

Runs the current quote follow-up loop:

1. Find active businesses for the configured tenant.
2. Detect stale quotes per business.
3. Emit idempotent `quote.stale` events.
4. Claim and dispatch pending events.
5. Write worker heartbeats when migration `000025_quote_runtime_hardening.sql` is applied.

Run once:

```bash
cd chromagora-os
PYTHONPATH=apps/api:packages/schemas:packages/config:packages/shared:apps/workers \
  python -m chromagora_workers.stale_quote_worker --once
```

Run continuously:

```bash
cd chromagora-os
PYTHONPATH=apps/api:packages/schemas:packages/config:packages/shared:apps/workers \
  python -m chromagora_workers.stale_quote_worker --interval 300
```

Optional stable worker identity:

```bash
python -m chromagora_workers.stale_quote_worker --worker-id stale-quote-prod-1
```

## Planned workers
- Agent runner — executes agent runs via LLM.
- Pipeline processor — handles workflow step execution.
- Scheduler/orchestrator — durable timers, leases, retries, and cross-worker supervision.
