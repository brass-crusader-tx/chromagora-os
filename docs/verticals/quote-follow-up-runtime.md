# Quote Follow-Up Runtime

This document describes the complete runtime loop for detecting and acting on stale quotes.

## Business Condition

A quote was sent to a customer. Time has passed without a response. The system detects the quote is stale, routes it through the agent architecture, requires approval, and upon approval creates a real internal task or message draft and updates the quote.

## Loop Shape

```
business state (quote is stale)
  → detector finds it
  → event emitted (quote.stale)
  → event dispatcher routes to handler
  → agent run created
  → context packet built and persisted
  → action proposal created
  → Tool Broker receives proposal
  → Policy Kernel evaluates authority
  → if approval required: real approval request created
  → operator approves or rejects
  → approved action executes (creates task or draft)
  → quote state updated
  → follow-up events emitted
  → ledger records the full lifecycle
  → trace_id connects everything
```

## Tables Involved

| Table | Role in This Loop |
|---|---|
| `quotes` | Subject of the loop. Extended with follow_up_count, next_follow_up_at, stale_detected_at, currency, description, accepted_at, declined_at, new statuses. |
| `events` | Carries quote.stale, quote.follow_up_proposed, quote.follow_up_approved, quote.follow_up_rejected, quote.follow_up_executed, quote.status_changed. Extended with idempotency_key, processed_at, entity_type, entity_id, status, claim/retry/dead-letter fields. |
| `agent_runs` | One run per quote.stale event processing. Records input, context, output. Connected via trace_id. |
| `action_proposals` | One proposal per processed quote.stale. Extended with quote_id, customer_id, agent_run_id, reason, requires_approval, policy_decision_id, idempotency_key. |
| `approval_requests` | One request when policy requires approval. Extended with title, summary, draft_payload, risk_level, agent_run_id, idempotency_key. |
| `action_executions` | Records what was executed. Extended with execution_mode and idempotent execution keys; supports running → success/failed. |
| `crm_tasks` | Target of create_task execution. Linked to quote, business, agent_run, proposal, approval, and idempotency key. |
| `message_drafts` | Target of create_message_draft execution. Extended with tenant_id, quote_id, customer_id, agent_run_id, approval_request_id, source, and idempotency key. |
| `business_preferences` | Stores follow-up settings per business (stale_threshold_days, max_follow_ups, requires_approval, preferred_channel, tone). |
| `authority_envelopes` | Evaluated by Policy Kernel. |
| `structured_logs` | Written by trace_propagation. |

## Services Involved

| Service | File | Role |
|---|---|---|
| Quote Stale Detector | `services/quote_stale_detector.py` | Finds eligible quotes, emits quote.stale event, marks quote stale. Idempotent via idempotency_key. |
| Event Dispatcher | `services/event_dispatcher.py` | Claims pending events, routes quote.stale to handler, marks processed only on success, retries/dead-letters failures. |
| Quote Stale Handler | `services/quote_stale_handler.py` | Creates agent run, builds context, makes deterministic decision, creates proposal, routes through Tool Broker. |
| Tool Broker | `services/tool_broker.py` | Evaluates policy via Policy Kernel. Creates real approval_request when required. Executes via action_executor when allowed. |
| Policy Kernel | `services/policy_kernel.py` | Evaluates authority envelope, business preferences, action type, risk level. Returns allowed/approval_required/blocked. |
| Action Executor | `services/action_executor.py` | Executes only approved proposals, creates crm_task or message_draft idempotently, updates quote follow_up_count/last_followup_at/status, emits events. |
| Context Builder | `services/context_builder.py` | Builds context packet with business info, customer info, quote info, authority, history. |
| Trace Propagation | `services/trace_propagation.py` | Ensures trace_id flows through all records. Writes structured logs. |

## Events Emitted

| Event Type | When | Key Payload |
|---|---|---|
| `quote.stale` | Detector finds eligible stale quote | quote_id, days_since_sent, follow_up_count |
| `quote.follow_up_proposed` | Agent creates action proposal | quote_id, proposal_id, action_type |
| `quote.follow_up_approved` | Operator approves | approval_id, proposal_id |
| `quote.follow_up_rejected` | Operator rejects | approval_id, proposal_id |
| `quote.follow_up_executed` | Execution completes | quote_id, action_type, execution_id |
| `quote.follow_up_failed` | Execution fails | quote_id, error |
| `quote.status_changed` | Quote status transitions | old_status, new_status, follow_up_count |

## Default Policy

| Action Type | Default Policy |
|---|---|
| `create_quote_follow_up_task` | Allowed (internal task, low risk) |
| `create_quote_follow_up_draft` | Approval required (customer-facing draft) |
| `send_quote_follow_up` | Blocked (no real sending adapter) |

## Approval Lifecycle

### Approve
1. `approval_requests.status` → `approved`
2. `action_proposals.status` → `approved`
3. `action_executor.execute_approved_action()` called
4. Task or draft created
5. Quote `follow_up_count` incremented
6. Quote `last_followup_at` set
7. Quote status → `follow_up_pending` (task) or `followed_up` (draft)
8. `quote.follow_up_executed` event emitted
9. `quote.status_changed` event emitted
10. Ledger records execution
11. `trace_id` preserved throughout

### Reject
1. `approval_requests.status` → `rejected`
2. `action_proposals.status` → `rejected`
3. No task or draft created
4. Quote `follow_up_count` not incremented
5. `quote.follow_up_rejected` event emitted
6. Ledger records rejection
7. `trace_id` preserved

## Quote Status Lifecycle

```
draft → sent → stale → follow_up_pending → followed_up → (accepted | declined | expired | cancelled)
                          ↘ (rejected by operator — stays stale, can re-detect)
```

Status `follow_up_pending` is used when a task has been created but not completed.
Status `followed_up` is used when a draft has been created (implies follow-up action taken).

## Business Follow-Up Settings

Stored in `business_preferences` with these keys:

| Key | Type | Default | Description |
|---|---|---|---|
| `stale_quote_threshold_days` | int | 3 | Days after sent_at before quote is stale |
| `max_quote_follow_ups` | int | 3 | Maximum follow-up attempts |
| `follow_up_interval_days` | int | 3 | Days to wait between repeat follow-up attempts |
| `quote_follow_up_requires_approval` | bool | true | Whether follow-up requires human approval |
| `preferred_follow_up_channel` | text | "email" | Channel for follow-up: email or sms |
| `follow_up_tone` | text | null | Tone hint for draft generation |

## How to Run the Demo

### Prerequisites
- Supabase instance with migrations 000001–000025 applied
- API server running
- Seed data loaded

### Steps

```bash
# 1. Apply migrations
# Run migrations 000024_quote_follow_up_runtime.sql and 000025_quote_runtime_hardening.sql against your Supabase instance

# 2. Seed data
cd chromagora-os
.venv/bin/python scripts/seed_data.py

# 3. Run one worker cycle (detects stale quotes and processes claimed events)
PYTHONPATH=apps/api:packages/schemas:packages/config:packages/shared:apps/workers \
  python -m chromagora_workers.stale_quote_worker --once

# Alternative manual detector + dispatcher:
curl -X POST http://localhost:8000/businesses/{business_id}/quotes/detect-stale
curl -X POST "http://localhost:8000/events/process?event_type=quote.stale"

# Expected: one quote.stale event claimed, processed, and converted into a proposal/approval.

# 4. Check pending approvals
curl http://localhost:8000/approvals?status=pending

# Expected: Array with one approval request including quote context

# 5. Approve the request
curl -X POST http://localhost:8000/approvals/{approval_id}/approve

# Expected: approval.status = "approved", execution_result with created task/draft

# 6. Verify the trace
curl http://localhost:8000/traces/{trace_id}

# Expected: All records connected by trace_id
```

### Verify Quote State

```bash
curl http://localhost:8000/businesses/{business_id}/quotes/{quote_id}
```

The quote should now show:
- `status`: "follow_up_pending" or "followed_up"
- `follow_up_count`: 1
- `last_followup_at`: recent timestamp
- `next_follow_up_at`: scheduled from `follow_up_interval_days` until the max is reached

## How to Run Tests

```bash
cd chromagora-os
.venv/bin/python -m pytest apps/api/tests/test_quote_follow_up_runtime.py -v
.venv/bin/python -m pytest -q
```

The focused quote follow-up suite plus full repo pytest run cover:
- Detector emits event (1 test)
- Detector idempotency (1 test)
- Detector ignores ineligible quotes (3 tests)
- Event dispatch creates agent run (1 test)
- Agent creates proposal (1 test)
- Approval required path creates real approval (1 test)
- Rejection does not execute (1 test)
- Trace integrity (1 test)
- Action executor creates task (1 test)
- Action executor creates draft (1 test)
- Action executor updates quote count (1 test)
- Route-level detect/process/trace/task endpoints
- Full repository regression coverage with live Supabase tests deselected by default

## Known Limitations

- **No external sending.** Approved execution creates an internal CRM task or message draft. No real email or SMS is sent. The loop is designed so real communication adapters can be attached later through Tool Broker.
- **Deterministic decisions.** The agent decision logic is template-based, not LLM-driven. This is intentional for v0.1 — runtime closure matters more than model cleverness.
- **Polling worker, not a durable orchestrator.** `apps/workers/chromagora_workers/stale_quote_worker.py` now runs detection plus event processing and writes heartbeats, but it is still a polling loop. It is not a Temporal-style durable workflow engine.
- **Context packet fallback.** If the full context builder fails (e.g., missing business twin), the handler falls back to event payload only. This degrades decision quality but doesn't break the loop.
- **Tenant isolation is database-scoped, not yet business-cell-native.** Runtime records are tenant/business scoped, but first-class Business Operating Cell constitution/capability records are still a follow-on architecture pivot.
- **No escalation.** If max follow-ups is reached, the system stops. No escalation to a human manager is implemented.
- **Tone is a hint, not enforced.** The `follow_up_tone` preference is stored but the deterministic draft generator doesn't vary output based on tone yet.
