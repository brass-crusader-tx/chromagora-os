"""Quote stale event handler — processes quote.stale events.

When a quote.stale event is dispatched, this handler:
1. Creates an agent run
2. Builds a context packet
3. Makes a deterministic decision about follow-up action
4. Creates an action proposal
5. Routes the proposal through Tool Broker
6. Returns the outcome
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_api.services.context_builder import build_context_packet
from chromagora_api.services.tool_broker import request_tool_execution
from chromagora_api.services.trace_propagation import ensure_trace_id, log_structured_event
from chromagora_api.services.runtime_utils import parse_json_field, run_awaitable_blocking, to_jsonable

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


def handle_quote_stale_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process a quote.stale event through the full agent loop.

    Steps:
    1. Create agent run
    2. Build context packet
    3. Determine follow-up action (deterministic for v0.1)
    4. Create action proposal
    5. Route through Tool Broker
    6. Return outcome

    Args:
        event: The event row from the events table.

    Returns:
        Dict with agent_run_id, proposal_id, tool_broker_outcome, trace_id.
    """
    sb = _get_supabase()
    if not sb:
        return {"status": "error", "error": "Database unavailable"}

    trace_id = event.get("trace_id") or ensure_trace_id()
    tenant_id = event.get("tenant_id")
    business_id = event.get("business_id")
    payload = parse_json_field(event.get("payload_json", {}), default={})

    quote_id = payload.get("quote_id")
    event_id = event.get("id")
    follow_up_count = payload.get("follow_up_count", 0)
    max_follow_ups = payload.get("max_follow_ups", 3)
    requires_approval = payload.get("requires_approval", True)
    preferred_channel = payload.get("preferred_follow_up_channel") or payload.get("preferred_channel", "email")
    days_since_sent = payload.get("days_since_sent", 0)

    proposal_idempotency_key = f"quote.follow_up_proposal:{quote_id}:{follow_up_count}"
    existing_proposal = _find_existing_proposal(sb, tenant_id, proposal_idempotency_key)
    if existing_proposal:
        return {
            "status": "completed",
            "duplicate": True,
            "proposal_id": existing_proposal.get("id"),
            "action_type": existing_proposal.get("action_type"),
            "requires_approval": existing_proposal.get("requires_approval"),
            "trace_id": existing_proposal.get("trace_id") or trace_id,
        }

    # ── Step 1: Create agent run ──────────────────────────────────────────
    agent_run_id = str(uuid4())
    try:
        sb.table("agent_runs").insert({
            "id": agent_run_id,
            "tenant_id": tenant_id,
            "business_id": business_id,
            "agent_type": "crm",
            "trigger_type": "event",
            "trigger_event_id": event_id,
            "status": "running",
            "input_json": {
                "event_type": "quote.stale",
                "quote_id": quote_id,
            },
            "trace_id": trace_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as exc:
        logger.error("Failed to create agent run: %s", exc)
        return {"status": "error", "error": f"Agent run creation failed: {exc}"}

    # ── Step 2: Build context packet ──────────────────────────────────────
    context_packet = None
    context_packet_id = str(uuid4())
    try:
        context_packet = run_awaitable_blocking(build_context_packet(
            business_id=UUID(business_id),
            task_type="customer_message_draft",
            actor_type="agent",
            actor_id=UUID(agent_run_id) if agent_run_id else None,
            objective=f"Process stale quote {quote_id}: determine follow-up action",
            tenant_id=UUID(tenant_id) if tenant_id else None,
            trace_id=trace_id,
        ))
        # Persist context packet as native JSON on the agent run.
        packet_json = to_jsonable(context_packet)
        sb.table("agent_runs").update({
            "context_packet_json": packet_json,
        }).eq("id", agent_run_id).execute()
    except Exception as exc:
        logger.warning("Context packet build failed (continuing with payload-only context): %s", exc)
        context_packet = {
            "packet_id": context_packet_id,
            "quote_payload": payload,
            "message": "Full context unavailable; using event payload",
        }

    # ── Step 3: Determine action (deterministic for v0.1) ────────────────
    decision = _determine_follow_up_action(
        payload=payload,
        requires_approval=requires_approval,
        preferred_channel=preferred_channel,
    )

    # ── Step 4: Create action proposal ────────────────────────────────────
    proposal_id = str(uuid4())
    try:
        sb.table("action_proposals").insert({
            "id": proposal_id,
            "tenant_id": tenant_id,
            "business_id": business_id,
            "proposed_by_type": "agent",
            "proposed_by_id": agent_run_id,
            "action_type": decision["action_type"],
            "title": decision["title"],
            "description": decision["description"],
            "proposed_payload": to_jsonable(decision["payload"]),
            "risk_level": decision["risk_level"],
            "autonomy_level_required": 2,
            "status": "proposed",
            "evidence_json": to_jsonable(decision["evidence"]),
            "trace_id": trace_id,
            "quote_id": quote_id,
            "customer_id": payload.get("customer_id"),
            "agent_run_id": agent_run_id,
            "reason": decision["reason"],
            "requires_approval": decision["requires_approval"],
            "idempotency_key": proposal_idempotency_key,
        }).execute()
    except Exception as exc:
        # If another worker created the same proposal between the read and insert,
        # return the existing proposal instead of creating duplicate work.
        existing_proposal = _find_existing_proposal(sb, tenant_id, proposal_idempotency_key)
        if existing_proposal:
            return {
                "status": "completed",
                "duplicate": True,
                "agent_run_id": agent_run_id,
                "proposal_id": existing_proposal.get("id"),
                "trace_id": existing_proposal.get("trace_id") or trace_id,
            }
        logger.error("Failed to create action proposal: %s", exc)
        _fail_agent_run(sb, agent_run_id, str(exc))
        return {"status": "error", "error": f"Proposal creation failed: {exc}"}

    # Emit quote.follow_up_proposed event
    _emit_event(sb, tenant_id, business_id, "quote.follow_up_proposed", "agent", agent_run_id,
                {"quote_id": quote_id, "proposal_id": proposal_id, "action_type": decision["action_type"]},
                trace_id)

    # ── Step 5: Route through Tool Broker ─────────────────────────────────
    tool_broker_outcome = None
    try:
        tool_broker_outcome = request_tool_execution(
            tenant_id=UUID(tenant_id),
            business_id=UUID(business_id),
            action_proposal_id=UUID(proposal_id),
            trace_id=trace_id,
        )
    except Exception as exc:
        logger.error("Tool Broker failed: %s", exc)
        _fail_agent_run(sb, agent_run_id, f"Tool Broker error: {exc}")
        return {
            "status": "error",
            "agent_run_id": agent_run_id,
            "proposal_id": proposal_id,
            "error": f"Tool Broker failed: {exc}",
            "trace_id": trace_id,
        }

    # ── Step 6: Complete agent run ────────────────────────────────────────
    outcome_status = tool_broker_outcome.get("outcome", "unknown") if tool_broker_outcome else "unknown"
    decision_summary = f"Proposed {decision['action_type']}. Tool Broker outcome: {outcome_status}"

    if outcome_status == "failed":
        error = tool_broker_outcome.get("error", "Tool Broker returned failed outcome") if tool_broker_outcome else "Tool Broker failed"
        _fail_agent_run(sb, agent_run_id, error)
        return {
            "status": "error",
            "agent_run_id": agent_run_id,
            "proposal_id": proposal_id,
            "error": error,
            "tool_broker_outcome": tool_broker_outcome,
            "trace_id": trace_id,
        }

    try:
        sb.table("agent_runs").update({
            "status": "completed",
            "output_json": to_jsonable({
                "proposal_id": proposal_id,
                "tool_broker_outcome": tool_broker_outcome,
                "decision": decision,
            }),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", agent_run_id).execute()
    except Exception as exc:
        logger.warning("Failed to complete agent run: %s", exc)

    return {
        "status": "completed",
        "agent_run_id": agent_run_id,
        "proposal_id": proposal_id,
        "action_type": decision["action_type"],
        "requires_approval": decision["requires_approval"],
        "tool_broker_outcome": tool_broker_outcome,
        "trace_id": trace_id,
    }


# ---------------------------------------------------------------------------
# Deterministic decision logic
# ---------------------------------------------------------------------------

def _determine_follow_up_action(
    payload: dict[str, Any],
    requires_approval: bool,
    preferred_channel: str,
) -> dict[str, Any]:
    """Decide what follow-up action to take.

    For v0.1 this is purely deterministic/template-based.
    LLM drafting is optional and not implemented here.
    """
    quote_id = payload.get("quote_id", "unknown")
    days_since_sent = payload.get("days_since_sent", 0)
    follow_up_count = payload.get("follow_up_count", 0)
    max_follow_ups = payload.get("max_follow_ups", 3)
    service_type = payload.get("service_type", "our services")
    quote_amount = payload.get("quote_amount")
    currency = payload.get("currency", "CAD")

    # Build the reason
    reason = (
        f"Quote was sent {days_since_sent} days ago. "
        f"Follow-up count is {follow_up_count} of {max_follow_ups}. "
        f"No response has been recorded."
    )

    # Decide action type based on channel and approval requirement
    # If approval is required, create a message draft for review
    # If not required, create a CRM task
    if requires_approval:
        action_type = "create_quote_follow_up_draft"
        # Build draft body
        customer_id = payload.get("customer_id")
        customer_name = _get_customer_name_from_payload(payload)
        recipient = _get_recipient_from_payload(payload, preferred_channel)
        draft_body = (
            f"Hi {customer_name}, "
            f"just following up on the quote for {service_type}"
            + (f" ({currency} {quote_amount:,.2f})" if quote_amount else "")
            + f". Let me know if you have any questions or if you'd like to move forward."
        )
        task_payload = {
            "channel": preferred_channel,
            "recipient": recipient,
            "subject": f"Following up on your {service_type} quote",
            "body": draft_body,
        }
    else:
        action_type = "create_quote_follow_up_task"
        task_title = "Follow up on sent quote"
        task_body = (
            f"Customer has not responded to the quote sent {days_since_sent} days ago "
            f"for {service_type}"
            + (f" ({currency} {quote_amount:,.2f})" if quote_amount else "")
            + f". Follow-up {follow_up_count + 1} of {max_follow_ups}."
        )
        task_payload = {
            "title": task_title,
            "description": task_body,
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }

    # Risk level: low for tasks, medium for customer-facing drafts
    risk_level = "medium" if requires_approval else "low"

    # Evidence for the decision
    evidence = {
        "days_since_sent": days_since_sent,
        "follow_up_count": follow_up_count,
        "max_follow_ups": max_follow_ups,
        "stale_threshold_days": payload.get("stale_threshold_days", 3),
        "quote_status": payload.get("status"),
        "requires_approval": requires_approval,
        "preferred_channel": preferred_channel,
    }

    return {
        "action_type": action_type,
        "title": "Quote follow-up proposed" if requires_approval else "Quote follow-up task",
        "description": reason,
        "reason": reason,
        "payload": task_payload,
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "evidence": evidence,
    }


def _get_customer_name_from_payload(payload: dict) -> str:
    """Extract a friendly customer name from the event payload."""
    customer_name = payload.get("customer_name")
    if isinstance(customer_name, str) and customer_name.strip():
        return customer_name.strip()
    return "there"


def _get_recipient_from_payload(payload: dict, preferred_channel: str) -> str:
    """Choose the best available recipient for the preferred channel."""
    if preferred_channel == "sms":
        candidates = (
            payload.get("contact_phone"),
            payload.get("customer_contact"),
            payload.get("contact_email"),
        )
    else:
        candidates = (
            payload.get("contact_email"),
            payload.get("customer_contact"),
            payload.get("contact_phone"),
        )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _find_existing_proposal(sb, tenant_id: str | None, idempotency_key: str) -> Optional[dict[str, Any]]:
    """Return an existing proposal for this quote/follow-up cycle, if any."""
    if not tenant_id or not idempotency_key:
        return None
    try:
        resp = (
            sb.table("action_proposals")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("idempotency_key", idempotency_key)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception:
        # Older databases may not have idempotency_key yet.
        return None


def _fail_agent_run(sb, agent_run_id: str, error: str) -> None:
    try:
        sb.table("agent_runs").update({
            "status": "failed",
            "error_message": error[:1000],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", agent_run_id).execute()
    except Exception:
        pass


def _emit_event(
    sb, tenant_id: str, business_id: str,
    event_type: str, source_type: str, source_id: str,
    payload: dict, trace_id: str,
) -> None:
    try:
        sb.table("events").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": business_id,
            "event_type": event_type,
            "source_type": source_type,
            "source_id": source_id,
            "payload_json": payload,
            "trace_id": trace_id,
        }).execute()
    except Exception as exc:
        logger.warning("Failed to emit %s event: %s", event_type, exc)
