"""ContextBuilder service — deterministic context assembly using Supabase."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_schemas.context import (
    ContextBudget,
    ContextPacket,
    EvidenceBundle,
    EvidenceItem,
    ModelTier,
    TaskType,
)

logger = logging.getLogger(__name__)

# Default budget per task type — conservative to avoid waste
_DEFAULT_BUDGETS: dict[TaskType, ContextBudget] = {
    TaskType.DETERMINISTIC_UPDATE: ContextBudget(
        max_input_tokens=2000, max_output_tokens=500, max_iterations=1,
        allow_retrieval=False, allow_full_artifacts=False, allow_subagents=False,
        escalation_model_tier=ModelTier.SMALL,
    ),
    TaskType.SIMPLE_CLASSIFICATION: ContextBudget(
        max_input_tokens=4000, max_output_tokens=1000, max_iterations=1,
        allow_retrieval=False, allow_full_artifacts=False, allow_subagents=False,
        escalation_model_tier=ModelTier.MEDIUM,
    ),
    TaskType.STRUCTURED_EXTRACTION: ContextBudget(
        max_input_tokens=6000, max_output_tokens=1500, max_iterations=1,
        allow_retrieval=True, allow_full_artifacts=False, allow_subagents=False,
        escalation_model_tier=ModelTier.MEDIUM,
    ),
    TaskType.CUSTOMER_MESSAGE_DRAFT: ContextBudget(
        max_input_tokens=8000, max_output_tokens=2000, max_iterations=2,
        allow_retrieval=True, allow_full_artifacts=True, allow_subagents=False,
        escalation_model_tier=ModelTier.STRONG,
    ),
    TaskType.APPROVAL_CARD_SUMMARY: ContextBudget(
        max_input_tokens=8000, max_output_tokens=2000, max_iterations=1,
        allow_retrieval=True, allow_full_artifacts=False, allow_subagents=False,
        escalation_model_tier=ModelTier.MEDIUM,
    ),
    TaskType.OPPORTUNITY_SCORING: ContextBudget(
        max_input_tokens=12000, max_output_tokens=3000, max_iterations=1,
        allow_retrieval=True, allow_full_artifacts=True, allow_subagents=False,
        escalation_model_tier=ModelTier.STRONG,
    ),
    TaskType.PROCUREMENT_ANALYSIS: ContextBudget(
        max_input_tokens=16000, max_output_tokens=4000, max_iterations=2,
        allow_retrieval=True, allow_full_artifacts=True, allow_subagents=True,
        escalation_model_tier=ModelTier.STRONG,
    ),
    TaskType.NEGOTIATION_PREP: ContextBudget(
        max_input_tokens=16000, max_output_tokens=4000, max_iterations=2,
        allow_retrieval=True, allow_full_artifacts=True, allow_subagents=True,
        escalation_model_tier=ModelTier.STRONG,
    ),
    TaskType.COMPLIANCE_SENSITIVE_ACTION: ContextBudget(
        max_input_tokens=12000, max_output_tokens=3000, max_iterations=1,
        allow_retrieval=True, allow_full_artifacts=True, allow_subagents=False,
        escalation_model_tier=ModelTier.HUMAN,
    ),
    TaskType.BINDING_COMMITMENT: ContextBudget(
        max_input_tokens=12000, max_output_tokens=3000, max_iterations=1,
        allow_retrieval=True, allow_full_artifacts=True, allow_subagents=False,
        escalation_model_tier=ModelTier.HUMAN,
    ),
}


def _get_supabase():
    """Get Supabase client from app state."""
    # Import lazily to avoid circular imports
    from chromagora_api.db import get_supabase
    return get_supabase()


def _truncate_events(events: list[dict], budget: ContextBudget) -> list[dict]:
    """Cap events to stay within token budget.

    Keeps only essential fields and limits count.
    """
    max_events = 10 if budget.max_input_tokens >= 8000 else 5
    truncated = []
    for ev in events[:max_events]:
        truncated.append({
            "event_type": ev.get("event_type"),
            "source_type": ev.get("source_type"),
            "occurred_at": str(ev.get("occurred_at", "")),
            "payload_json": ev.get("payload_json", {}),
        })
    return truncated


def _build_evidence_from_events(
    events: list[dict],
) -> EvidenceBundle:
    """Derive an evidence bundle from action/event references."""
    items: list[EvidenceItem] = []
    missing: list[str] = []

    for ev in events:
        payload = ev.get("payload_json", {})
        source_id = ev.get("source_id")
        items.append(EvidenceItem(
            source_type=ev.get("source_type", "event"),
            source_id=source_id,
            title=payload.get("title", ev.get("event_type", "unknown")),
            snippet=payload.get("snippet", "")[:200],
            url=payload.get("url"),
            confidence=0.8 if source_id else 0.5,
        ))

    return EvidenceBundle(
        evidence_items=items,
        missing_evidence=missing,
        confidence=min((i.confidence for i in items), default=1.0),
        source_summary=f"{len(items)} events referenced",
    )


async def build_context_packet(
    business_id: UUID,
    task_type: TaskType,
    actor_type: str,
    actor_id: Optional[UUID],
    objective: str,
    requested_model_tier: ModelTier | int,
    workflow_run_id: Optional[UUID] = None,
    action_proposal_id: Optional[UUID] = None,
    event_ids: Optional[list[UUID]] = None,
) -> ContextPacket:
    """Build a ContextPacket by querying Supabase for business state.

    This is deterministic — no LLM calls, no vector retrieval.
    """
    if isinstance(requested_model_tier, int):
        requested_model_tier = ModelTier(requested_model_tier)

    budget = _DEFAULT_BUDGETS.get(task_type, ContextBudget())
    sb = _get_supabase()

    # 1. Load business twin slice
    twin_slice: dict[str, Any] = {}
    try:
        resp = (
            sb.table("business_twin")
            .select("status, current_phase, capacity_score, active_claims_count, "
                    "lifetime_value, churn_risk, last_activity_at")
            .eq("business_id", str(business_id))
            .execute()
        )
        if resp.data:
            twin_slice = resp.data[0]
    except Exception as exc:
        logger.warning("Failed to load business_twin: %s", exc)

    # 2. Load active claims (approved + forbidden)
    approved_claims: list[dict] = []
    forbidden_claims: list[dict] = []
    try:
        resp = (
            sb.table("claims")
            .select("id, claim_type, status, amount, description, created_at")
            .eq("business_id", str(business_id))
            .in_("status", ["approved", "forbidden"])
            .execute()
        )
        for c in resp.data or []:
            if c.get("status") == "approved":
                approved_claims.append(c)
            else:
                forbidden_claims.append(c)
    except Exception as exc:
        logger.warning("Failed to load claims: %s", exc)

    # 3. Load recent events (capped by budget)
    relevant_events: list[dict] = []
    try:
        query = (
            sb.table("events")
            .select("id, event_type, source_type, source_id, occurred_at, payload_json")
            .eq("business_id", str(business_id))
            .order("occurred_at", desc=True)
            .limit(20)
        )
        if event_ids:
            query = query.in_("id", [str(eid) for eid in event_ids])
        resp = query.execute()
        relevant_events = _truncate_events(resp.data or [], budget)
    except Exception as exc:
        logger.warning("Failed to load events: %s", exc)

    # 4. Build evidence bundle
    evidence = _build_evidence_from_events(relevant_events)

    # 5. Assemble packet
    return ContextPacket(
        packet_id=uuid4(),
        tenant_id=UUID(twin_slice.get("tenant_id", "00000000-0000-0000-0000-000000000000")),
        business_id=business_id,
        task_type=task_type,
        actor_type=actor_type,
        actor_id=actor_id,
        model_tier=requested_model_tier,
        context_budget=budget,
        objective=objective,
        business_twin_slice=twin_slice,
        workflow_state={"workflow_run_id": str(workflow_run_id)} if workflow_run_id else {},
        relevant_events=relevant_events,
        evidence_bundle=evidence,
        approved_claims=approved_claims[:5],
        forbidden_claims=forbidden_claims[:5],
        created_at=datetime.now(timezone.utc),
    )
