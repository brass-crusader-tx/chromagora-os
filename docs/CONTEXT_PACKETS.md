# Context Economy

## Overview

The Context Economy Layer is the token-efficiency backbone of Chromagora OS. It ensures that every LLM call carries only the minimum necessary context — no full transcripts, no unrelated state, no wasted tokens.

## ContextPacket

A `ContextPacket` is the atomic unit of work passed to an LLM or agent. It contains:

| Field | Purpose |
|-------|---------|
| `packet_id` | Unique identifier for tracing |
| `tenant_id` | Tenant isolation |
| `business_id` | The business this packet is about |
| `task_type` | What kind of task (deterministic, extraction, draft, etc.) |
| `actor_type` / `actor_id` | Who initiated the task |
| `model_tier` | Which model tier to use (selected by TokenBudgetPolicy) |
| `context_budget` | Token and iteration limits |
| `objective` | The specific goal |
| `authority_summary` | What the actor is authorized to do |
| `business_twin_slice` | Relevant subset of the Business Twin |
| `workflow_state` | Current workflow position |
| `relevant_events` | Capped list of recent events |
| `evidence_bundle` | Structured evidence with confidence |
| `retrieved_artifacts` | Full artifacts (only if budget allows) |
| `forbidden_claims` | Claims that must not be violated |
| `approved_claims` | Pre-approved claims for this context |
| `output_schema_name` | Expected output schema |
| `escalation_conditions` | When to escalate to a stronger model or human |

## ContextBudget

Controls resource consumption:

- `max_input_tokens` — how much context to feed in
- `max_output_tokens` — how much output to expect
- `max_iterations` — how many LLM turns allowed
- `allow_retrieval` — whether external data retrieval is permitted
- `allow_full_artifacts` — whether full documents can be included
- `allow_subagents` — whether the task can spawn subagents
- `escalation_model_tier` — which tier to escalate to if needed

## EvidenceBundle

Structured evidence with confidence scoring:

- `evidence_items` — individual pieces of evidence
- `missing_evidence` — what evidence is still needed
- `confidence` — aggregate confidence (0.0 to 1.0)
- `source_summary` — human-readable summary of sources

## TokenBudgetPolicy

Deterministic model tier selection based on:

1. **Task type** — base tier assignment
2. **Risk level** — high risk escalates
3. **Dollar exposure** — higher exposure → stronger model
4. **Compliance sensitivity** — compliance tasks need stronger models or humans
5. **Confidence** — low confidence escalates one tier
6. **Missing evidence** — missing evidence escalates one tier

### Tier Ladder

```
NO_MODEL (0) → SMALL (1) → MEDIUM (2) → STRONG (3) → HUMAN (4)
```

Each step up costs more but adds capability. The system always starts at the lowest sufficient tier.

## ContextBuilder

The `ContextBuilder` service assembles context packets deterministically:

1. Queries Supabase for the Business Twin slice
2. Loads active claims (approved + forbidden)
3. Loads recent events (capped by budget)
4. Builds an evidence bundle from event references
5. Returns a complete ContextPacket

**No LLM calls. No vector retrieval. No full transcripts.**

## Design Principles

- **Compactness**: Every field must earn its place. If it doesn't help the LLM make a better decision, it doesn't go in the packet.
- **Determinism**: Context assembly is purely deterministic. Same inputs → same packet.
- **Budget-aware**: The packet knows its own constraints and won't exceed them.
- **Evidence-first**: Claims and evidence are structured, not free-text. Confidence is explicit.
- **Escalation over guessing**: When uncertain, escalate to a stronger model or human rather than guess.
