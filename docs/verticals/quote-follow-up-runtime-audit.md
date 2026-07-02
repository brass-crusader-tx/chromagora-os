# Quote Follow-Up Runtime Loop — Audit Document

**Status:** Draft  
**Scope:** Full runtime loop for automated quote follow-up, from stale detection through action execution and outcome recording.  
**Baseline:** Migrations 000001–000023, current service layer as of 2026-06-26.

---

## 1. Purpose

This document records the findings of a comprehensive audit of the codebase against the requirements of an automated quote follow-up runtime loop. The loop is expected to:

1. Detect quotes that have become stale (no response within a configurable threshold).
2. Propose a follow-up action for each stale quote.
3. Route the action through the correct approval or execution path based on business policy and autonomy level.
4. Execute the follow-up (e.g., send a message draft, apply a discount, escalate to a human).
5. Record the outcome and update the quote state.
6. Maintain full traceability from detection through outcome via trace IDs and structured logging.

The audit identifies every gap, bug, and missing capability that prevents this loop from running end-to-end in production.

---

## 2. Methodology

The audit examined:

- All database migrations from `000001` through `000023` to catalogue every table, column, index, and constraint.
- All service modules in the vertical runtime layer: `tool_broker`, `policy_kernel`, `sales_agent`, `context_builder`, `agent_runs`, `trace_propagation`, `crm_service`, and the approvals route handler.
- Cross-cutting concerns: idempotency, event dispatch, approval lifecycle, and trace propagation.

Each finding is classified as either a **Gap** (something that does not exist yet) or a **Bug** (something that exists but is incorrect).

---

## 3. Table-by-Table Findings

### 3.1 `quotes`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 1 | Missing `tenant_id` — the quote cannot be scoped to a tenant, which breaks multi-tenant isolation for all downstream queries. | Gap | Critical |
| 2 | Missing `customer_id` — there is no direct FK to the customer/lead record; follow-up targeting must join through `lead_id` every time. | Gap | High |
| 3 | Missing `currency` — follow-up actions that involve dollar amounts (discounts, escalations) cannot reason about currency. | Gap | Medium |
| 4 | Missing `description` — there is no human-readable summary of what the quote covers, which makes action proposals and message drafts less informative. | Gap | Low |
| 5 | Missing `accepted_at` / `declined_at` timestamps — the system cannot distinguish between a quote that was explicitly declined and one that is merely unresponsive. | Gap | Medium |
| 6 | Missing `follow_up_count` — the system cannot enforce a maximum number of follow-up attempts per quote. | Gap | Critical |
| 7 | Missing `next_follow_up_at` — the system cannot schedule the next follow-up or query for "quotes due for follow-up." | Gap | Critical |
| 8 | Missing `stale_detected_at` — the system cannot record when staleness was first identified, which is needed for metrics and threshold tuning. | Gap | High |
| 9 | Status enum is too narrow. Current values: `draft`, `sent`, `accepted`, `rejected`, `stale`. Missing: `follow_up_pending`, `follow_up_sent`, `expired`, `cancelled`. Without these, the loop cannot represent its own intermediate states. | Gap | Critical |

### 3.2 `events`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 10 | Missing `idempotency_key` — without this, duplicate event dispatches (e.g., from retries) will create duplicate follow-up actions. | Gap | Critical |
| 11 | Missing `processed_at` — there is no way to distinguish events that have been consumed from those still pending. | Gap | High |
| 12 | Missing `entity_type` / `entity_id` — generic entity reference is absent, so consumers cannot efficiently query "all events for quote X." | Gap | High |

### 3.3 `action_proposals`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 13 | Missing `quote_id` — the proposal cannot be directly linked back to the quote it was generated for. | Gap | Critical |
| 14 | Missing `customer_id` — the proposal cannot directly reference the customer for targeting. | Gap | High |
| 15 | Missing `agent_run_id` — there is no link to the agent run that generated the proposal, breaking traceability. | Gap | High |
| 16 | Missing `reason` — there is no human-readable explanation for why the proposal was created (e.g., "quote stale for 7 days"). | Gap | Medium |
| 17 | Missing `requires_approval` — the proposal does not carry its own approval flag, so downstream consumers must re-derive this from policy. | Gap | Medium |
| 18 | Missing `policy_decision_id` — there is no record of which policy decision authorized this proposal, making audit trails incomplete. | Gap | Medium |

### 3.4 `approval_requests`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 19 | Missing `title` — approvers see no human-readable summary in the approval queue. | Gap | Medium |
| 20 | Missing `summary` — longer-form context for the approver is absent. | Gap | Medium |
| 21 | Missing `draft_payload` — the actual content to be sent/executed is not stored with the approval record, so approvers cannot review what they are approving. | Gap | High |
| 22 | Missing `risk_level` — approvers cannot quickly assess risk without loading related records. | Gap | Medium |
| 23 | Missing `agent_run_id` — traceability from approval back to the originating agent run is broken. | Gap | High |

### 3.5 `action_executions`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 24 | Missing `execution_mode` — there is no way to distinguish a dry-run execution from a real execution. This is needed for safe testing in production-like environments. | Gap | High |

### 3.6 `message_drafts`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 25 | Missing `tenant_id` — multi-tenant isolation is broken. | Gap | Critical |
| 26 | Missing `quote_id` — drafts cannot be traced back to the quote they were generated for. | Gap | Critical |
| 27 | Missing `customer_id` — drafts cannot directly reference the recipient customer. | Gap | High |
| 28 | Missing `agent_run_id` — traceability from draft to agent run is absent. | Gap | High |
| 29 | Missing `approval_request_id` — there is no link to the approval that authorized this draft. | Gap | Medium |
| 30 | Missing `source` — the origin of the draft (e.g., "stale_quote_followup", "manual") is not recorded. | Gap | Low |

### 3.7 `context_builder`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 31 | Queries a table named `claims` that does not exist in any migration. The correct tables are `approved_business_claims` and `forbidden_business_claims`. This will raise a database error at runtime. | Bug | Critical |

### 3.8 `business_preferences`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 32 | No preferences exist for follow-up configuration. Missing keys: `stale_threshold_days`, `max_follow_ups`, `follow_up_interval_days`, `auto_decline_on_expiry`, `escalation_agent_definition_id`. | Gap | High |

### 3.9 `crm_tasks`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 33 | No `crm_tasks` table exists. The system cannot create tasks (e.g., "call customer about quote") that are separate from message drafts. | Gap | Medium |

---

## 4. Service-by-Service Findings

### 4.1 `tool_broker.py` — `request_tool_execution`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 34 | When `approval_required` is true, the function creates an `action_proposal` and an `action_execution` record but does **not** create an `approval_request`. The proposal has no approval record to wait for, so the execution can never be unblocked. | Bug | Critical |
| 35 | When the tool is allowed without approval, the function performs a dry-run only. There is no real execution path — the tool is never actually invoked. | Gap | Critical |
| 36 | No mechanism exists to resume execution after approval. The function does not check for a previously approved request and continue. | Gap | High |

### 4.2 `policy_kernel.py` — `evaluate_action_policy`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 37 | No findings. The function correctly evaluates authority envelopes and compliance rules. | — | — |

### 4.3 `sales_agent.py` — `run_stale_quote_followup`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 38 | Uses `asyncio.run()` to call the context builder, which is an async function being run inside what may already be an async context. This will raise a runtime error if called from an event loop. | Bug | High |
| 39 | Always operates in `dry_run` mode — no real follow-up is ever sent. | Gap | High |
| 40 | Creates an agent run record but does not dispatch a real event to trigger downstream processing. The function is self-contained rather than participating in the event-driven architecture. | Gap | High |
| 41 | Does not read follow-up preferences from `business_preferences` — uses hardcoded or no thresholds. | Gap | Medium |

### 4.4 `context_builder.py` — `build_context_packet`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 42 | Queries non-existent `claims` table (see finding 31). | Bug | Critical |
| 43 | Does not include quote-specific context (amount, service type, days since sent) in the packet. | Gap | Medium |

### 4.5 `agent_runs.py` — `start_run` / `complete_run` / `fail_run`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 44 | No findings. Agent run lifecycle is correctly managed. | — | — |

### 4.6 `trace_propagation.py` — `ensure_trace_id` / `log_structured_event` / `propagate_trace` / `get_records_by_trace`

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 45 | No findings. Trace propagation is correctly implemented. | — | — |

### 4.7 `crm_service.py` — CRUD for leads, quotes, jobs, message_drafts

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 46 | CRUD operations are functionally correct but operate on the incomplete schemas documented in Section 3. | — | — |

### 4.8 Approvals Route — Approve / Reject Handlers

| # | Finding | Type | Severity |
|---|---------|------|----------|
| 47 | Approving an `approval_request` only updates the approval status. It does **not** continue the action execution lifecycle: no task is created, no quote is updated, no event is dispatched, and no `action_execution` record is transitioned. The approved action is effectively orphaned. | Bug | Critical |
| 48 | Rejecting an `approval_request` only updates the approval status. It does **not** update the related `action_proposal` status, create a notification, or record the rejection reason on the proposal. | Bug | High |

---

## 5. Cross-Cutting Gaps

### 5.1 No Quote Stale Detector Service

There is no service that periodically queries for quotes that have passed the stale threshold and emits `quote.stale` events. This is the entry point of the entire loop.

**Required behavior:**
- Query quotes where `status = 'sent'` and `sent_at + stale_threshold_days < now()`.
- Emit a `quote.stale` event with `entity_type = 'quote'` and `entity_id = <quote_id>`.
- Update the quote's `stale_detected_at` timestamp.
- Respect per-business `stale_threshold_days` from `business_preferences`.

### 5.2 No Event Dispatch Handler for `quote.stale`

Even if a `quote.stale` event were emitted, no handler exists to consume it and trigger the follow-up flow.

**Required behavior:**
- Listen for `quote.stale` events.
- Build a context packet for the quote.
- Evaluate policy to determine the action type.
- Create an `action_proposal` with `quote_id`, `customer_id`, `agent_run_id`, and `reason`.
- If approval is required, create an `approval_request`.
- If no approval is required, create an `action_execution` and proceed.

### 5.3 No Follow-Up Outcome Recording

After a follow-up is executed, there is no mechanism to:
- Update `quote.last_follow_up_at`.
- Increment `quote.follow_up_count`.
- Set `quote.next_follow_up_at` based on `follow_up_interval_days`.
- Transition quote status to `follow_up_sent` or `expired`.

### 5.4 No Idempotency on Event Processing

Without an `idempotency_key` on the `events` table, duplicate deliveries (from at-least-once messaging) will create duplicate follow-up actions. This is a correctness risk in any production deployment.

---

## 6. Dependency Graph for Remediation

The following ordering reflects logical dependencies — later items depend on earlier items being complete.

```
Phase 1: Schema Foundation
  ├── Migration 000024 — extend quotes table (findings 1-9)
  ├── Migration 000024 — extend events table (findings 10-12)
  ├── Migration 000024 — extend action_proposals (findings 13-18)
  ├── Migration 000024 — extend approval_requests (findings 19-23)
  ├── Migration 000024 — extend action_executions (finding 24)
  ├── Migration 000024 — extend message_drafts (findings 25-30)
  ├── Migration 000024 — add follow-up preferences to business_preferences (finding 32)
  └── Migration 000024 — create crm_tasks table (finding 33)

Phase 2: Bug Fixes
  ├── Fix context_builder claims table query (findings 31, 42)
  └── Fix sales_agent asyncio.run usage (finding 38)

Phase 3: Service Construction
  ├── Build quote_stale_detector service (Section 5.1)
  ├── Build event dispatch handler for quote.stale (Section 5.2)
  ├── Build follow-up outcome recorder (Section 5.3)
  └── Add idempotency key to event processing (Section 5.4)

Phase 4: Service Rewrites
  ├── Rewrite tool_broker to create approval_requests (finding 34)
  ├── Add real execution path to tool_broker (finding 35)
  ├── Add post-approval resume to tool_broker (finding 36)
  ├── Rewrite sales_agent to be event-driven (findings 39-41)
  ├── Fix approval route to continue action lifecycle on approve (finding 47)
  └── Fix approval route to update proposal on reject (finding 48)

Phase 5: Validation
  ├── Schema tests for all new columns and tables
  ├── Service unit tests for stale detector, event handler, tool_broker
  ├── Integration test: full loop from stale detection to outcome recording
  ├── Trace propagation verification across the full loop
  └── Seed data for test businesses with follow-up preferences
```

---

## 7. Summary Statistics

| Category | Count |
|----------|-------|
| Total findings | 48 |
| Bugs (existing code is incorrect) | 6 |
| Gaps (missing capabilities) | 42 |
| Critical severity | 10 |
| High severity | 18 |
| Medium severity | 15 |
| Low severity | 5 |
| Tables needing extension | 6 |
| Services needing construction | 4 |
| Services needing rewrite | 3 |
| Routes needing fix | 1 |

---

## 8. Risk Assessment

The quote follow-up runtime loop **cannot execute end-to-end** in the current state. The blockers are:

1. **No entry point.** Without a stale detector and event dispatch, nothing triggers the loop.
2. **No schema support.** The quotes, events, action_proposals, approval_requests, action_executions, and message_drafts tables all lack columns required by the loop.
3. **Broken approval lifecycle.** Even if an approval were created, approving it does not continue execution.
4. **No real execution path.** The tool broker only performs dry-runs.
5. **Critical bug.** The context builder will crash at runtime due to the non-existent `claims` table query.

All five categories of blocker must be resolved before the loop can function. The schema changes (Phase 1) are the highest-leverage investment because they unblock work in every subsequent phase.

---

## 9. Recommended Next Steps

1. **Approve Migration 000024** — this is the single largest unblocker. All schema extensions should be consolidated into one migration to minimize downtime and migration complexity.
2. **Fix the context_builder bug immediately** — this is a runtime crash that affects any code path using `build_context_packet`, not just the follow-up loop.
3. **Build the quote_stale_detector and event handler** — these are the entry points for the loop and can be tested independently of the approval/execution path.
4. **Rewrite tool_broker and approval routes** — these are the final pieces that close the loop from proposal through execution.
5. **Write integration tests** — the full loop should be verified end-to-end with trace propagation checks before any production deployment.

---

*End of audit document.*
