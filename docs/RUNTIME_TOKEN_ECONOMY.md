# Chromagora OS — Token Efficiency as Runtime Architecture

## Token efficiency is architecture, not optimization.

Token efficiency in Chromagora OS means using inference budgets intentionally based on task class and risk. It is not about spending the least possible tokens — it is about dividing the available budget across run types and risk levels.

### Spend fewer agents/tokens by default:
- deterministic code for deterministic tasks
- compact Context Packets not full state
- Business Twin slices, not the whole twin
- cached summaries and evidence bundles
- simple tasks to cheap/free models
- agent-to-agent event-based coordination, not chat loops

### Spend whatever is required when:
- correctness depends on it
- business performance is at stake
- trust, compliance, or money is on the line
- customer commitments or external actions are involved
- irreversible actions are proposed

## Context Packet

Agents receive Context Packets, not raw database access. A Context Packet is a typed, compact structure containing exactly what the agent needs and nothing more:

| Field | Source |
|-------|--------|
| relevant_business_twin_slice | Supabase query (filtered columns, scoped rows) |
| relevant_events | Supabase query (capped by count and relevance) |
| evidence_bundle | Structured evidence from ledger references |
| workflow_state | Current WorkflowRun state |
| authority_summary | Derived from AuthorityEnvelope |
| approved_claims | Filtered to relevant types |
| forbidden_claims | Filtered to relevant types |
| active_compliance_rules | Scoped to action type and jurisdiction |
| output_schema_name | Required response schema from SpawnContract |

Context Packets must be compact enough for the model tier assigned. A Tier 1 task gets a smaller packet than a Tier 3 task.

## Model Routing Tiers

```
Tier 0 — No model
  Deterministic: CRUD, routing, status transitions, timers, policy checks, event emission.

Tier 1 — Small/free model (e.g., gemma-4-26b-it:free on OpenRouter)
  Classification, entity extraction, formatting, simple drafting, note cleanup.

Tier 2 — Mid/free model (e.g., qwen/qwen3-coder:free on OpenRouter)
  Opportunity scoring, customer nuance, bid/no-bid reasoning, content drafting,
  approval card summaries, structured extraction.

Tier 3 — Strong/free model (e.g., nemotron-3-super-120b:free on OpenRouter)
  Complex procurement analysis, ambiguous customer situations, negotiation prep,
  high-value decisions, strategic reasoning.

Tier 4 — Human
  Physical inspection, irreversible commitments, legal/commercial approval,
  unusual pricing, trust transfer, voice escalation.
```

## Escalation Triggers

Escalate model tier when:
- confidence is below threshold
- evidence is incomplete
- dollar exposure exceeds limit
- compliance sensitivity is high
- customer sentiment is negative
- action is irreversible
- opportunity value is high (>= $10,000)
- agent disagreement occurs (two agents propose conflicting actions)
- policy requires approval

## Downgrade Rules

Downgrade is allowed when:
- all evidence is present
- confidence is high
- action is reversible
- dollar exposure is low
- task is well-defined with clear output schema
- historical accuracy for this task type is high

## Token Budget Per Agent Run

```python
@dataclass
class TokenBudget:
    max_input_tokens: int
    max_output_tokens: int
    max_iterations: int
    allow_retrieval: bool
    allow_full_artifacts: bool
    allow_subagents: bool
    escalation_model_tier: Optional[int]
```

Defaults per tier:
- Tier 1: 4096 input / 1024 output / 3 iterations
- Tier 2: 16384 input / 4096 output / 5 iterations
- Tier 3: 65536 input / 16384 output / 10 iterations

## Evidence Bundles

Evidence Bundles compactly summarize what is known, what is missing, and the confidence level:

```python
@dataclass
class EvidenceBundle:
    evidence_items: List[EvidenceItem]
    missing_evidence: List[str]
    confidence: float
    source_summary: str
```

Rules:
- Missing evidence is always reported to the operator
- Actions proposed with missing evidence must be flagged in the Approval Card
- If missing evidence prevents informed action, approval is required or the action is blocked

## What Token Efficiency Must Never Compromise

- Model quality when the task genuinely requires it
- Context completeness for compliance-sensitive or irreversible actions
- Policy Kernel or Tool Broker enforcement levels
- Escalation triggers and thresholds
- Explicit missing-evidence reporting

## Examples

### Good token efficiency
- Reputation Agent v0 (Tier 0) processes a review request through deterministic code. No model call. Context Packet is built from Supabase queries. Dry-run ActionExecution is recorded.

### Good token efficiency
- Sales Agent v0 stale quote check (Tier 0) performs simple date math. No model call.

### Good token efficiency
- Procurement Scout v0 scores a tender with rule-based logic (Tier 0) and creates a proposal. Only the approval card summary uses a Tier 2 model.

### Bad token efficiency
- Routing a $50,000 procurement analysis to a tier 1 model because "it's just extraction."

### Bad token efficiency
- Sending the entire Business Twin and all 500 events to every agent for every task.

### Bad token efficiency
- Allowing agents to summarize away compliance constraints to save tokens.
