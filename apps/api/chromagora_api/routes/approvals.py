"""Approval Inbox API routes.

Approve/reject now continues the action lifecycle:
- Approve → execution of the approved action, state mutation, events
- Reject → proposal rejected, no execution, rejection event emitted
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_tenant_id, get_backend_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _emit_approval_execution_failure(
    sb, tenant_id: str, business_id: str | None, action_proposal_id: str,
    approval_id: UUID, error: str, trace_id: str,
) -> None:
    try:
        sb.table("events").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": business_id,
            "event_type": "quote.follow_up_failed",
            "source_type": "execution",
            "source_id": action_proposal_id,
            "payload_json": {
                "approval_id": str(approval_id),
                "action_proposal_id": action_proposal_id,
                "error": error,
            },
            "trace_id": trace_id,
        }).execute()
    except Exception:
        pass


@router.get("")
async def list_approvals(status: str | None = None):
    """List approval requests, filtered by status."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    query = (
        sb.table("approval_requests")
        .select("*, action_proposals(*)")
        .eq("tenant_id", tenant_id)
        .order("requested_at", desc=True)
    )
    if status:
        query = query.eq("status", status)

    resp = query.execute()
    for row in (resp.data or []):
        proposal = row.get("action_proposals") or {}
        row["action_type"] = proposal.get("action_type") or proposal.get("title") or "approval"
        row["description"] = proposal.get("description")
        row["dollar_amount"] = proposal.get("expected_value")
        row["created_at"] = row.get("requested_at") or row.get("created_at", "")
        row["resolved_at"] = row.get("decided_at")
        # Expose quote follow-up context
        row["quote_id"] = proposal.get("quote_id")
        row["risk_level"] = row.get("risk_level") or proposal.get("risk_level")
        row["reason"] = proposal.get("reason")
        row["proposed_payload"] = proposal.get("proposed_payload")
    return resp.data or []


@router.post("/{approval_id}/approve")
async def approve_request(approval_id: UUID, decision_notes: str = ""):
    """Approve an approval request and execute the approved action."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Load the approval request first
    resp = (
        sb.table("approval_requests")
        .select("*")
        .eq("id", str(approval_id))
        .eq("tenant_id", tenant_id)
        .eq("status", "pending")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Approval request not found or already decided")
    approval = resp.data[0]

    trace_id = approval.get("trace_id") or str(uuid4())
    action_proposal_id = approval.get("action_proposal_id")
    business_id = approval.get("business_id")

    # Update approval request status
    now_iso = datetime.now(timezone.utc).isoformat()
    sb.table("approval_requests").update({
        "status": "approved",
        "decided_by": "operator",
        "decided_at": now_iso,
        "decision_notes": decision_notes,
    }).eq("id", str(approval_id)).execute()

    # Update proposal status
    if action_proposal_id:
        try:
            sb.table("action_proposals").update({
                "status": "approved",
                "updated_at": now_iso,
            }).eq("id", action_proposal_id).execute()
        except Exception as exc:
            logger.warning("Failed to update proposal status: %s", exc)

    # Emit approval event
    try:
        sb.table("events").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": business_id,
            "event_type": "quote.follow_up_approved",
            "source_type": "operator",
            "source_id": str(approval_id),
            "entity_type": "action_proposal",
            "entity_id": action_proposal_id,
            "payload_json": {
                "approval_id": str(approval_id),
                "action_proposal_id": action_proposal_id,
                "decision": "approved",
            },
            "trace_id": trace_id,
        }).execute()
    except Exception as exc:
        logger.warning("Failed to emit approval event: %s", exc)

    # ── Execute the approved action ───────────────────────────────────────
    execution_result = None
    if action_proposal_id:
        try:
            from chromagora_api.services.action_executor import execute_approved_action
            execution_result = execute_approved_action(
                action_proposal_id=UUID(action_proposal_id),
                approval_request_id=approval_id,
                trace_id=trace_id,
            )
            if execution_result.get("status") != "success":
                _emit_approval_execution_failure(
                    sb, tenant_id, business_id, action_proposal_id, approval_id,
                    execution_result.get("error", "Execution failed"), trace_id,
                )
        except Exception as exc:
            logger.exception("Post-approval execution failed: %s", exc)
            _emit_approval_execution_failure(
                sb, tenant_id, business_id, action_proposal_id, approval_id, str(exc), trace_id,
            )
            execution_result = {"status": "failed", "error": str(exc)}

    return {
        **approval,
        "status": "approved",
        "decided_by": "operator",
        "decided_at": now_iso,
        "execution_result": execution_result,
        "execution_status": (execution_result or {}).get("status"),
    }


@router.post("/{approval_id}/reject")
async def reject_request(approval_id: UUID, decision_notes: str = ""):
    """Reject an approval request — no action is executed."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Load the approval request
    resp = (
        sb.table("approval_requests")
        .select("*")
        .eq("id", str(approval_id))
        .eq("tenant_id", tenant_id)
        .eq("status", "pending")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Approval request not found or already decided")
    approval = resp.data[0]

    trace_id = approval.get("trace_id") or str(uuid4())
    action_proposal_id = approval.get("action_proposal_id")
    business_id = approval.get("business_id")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Update approval request status
    sb.table("approval_requests").update({
        "status": "rejected",
        "decided_by": "operator",
        "decided_at": now_iso,
        "decision_notes": decision_notes,
    }).eq("id", str(approval_id)).execute()

    # Update proposal status to rejected
    if action_proposal_id:
        try:
            sb.table("action_proposals").update({
                "status": "rejected",
                "updated_at": now_iso,
            }).eq("id", action_proposal_id).execute()
        except Exception as exc:
            logger.warning("Failed to update proposal status: %s", exc)

    # Emit rejection event
    try:
        sb.table("events").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": business_id,
            "event_type": "quote.follow_up_rejected",
            "source_type": "operator",
            "source_id": str(approval_id),
            "entity_type": "action_proposal",
            "entity_id": action_proposal_id,
            "payload_json": {
                "approval_id": str(approval_id),
                "action_proposal_id": action_proposal_id,
                "decision": "rejected",
            },
            "trace_id": trace_id,
        }).execute()
    except Exception as exc:
        logger.warning("Failed to emit rejection event: %s", exc)

    # Write to ledger
    try:
        from chromagora_api.services.trace_propagation import log_structured_event
        log_structured_event(
            tenant_id=UUID(tenant_id),
            trace_id=trace_id,
            service_name="approval",
            event_type="quote.follow_up_rejected",
            message=f"Approval {approval_id} rejected — no action executed",
            context={"action_proposal_id": action_proposal_id},
        )
    except Exception:
        pass

    return {
        **approval,
        "status": "rejected",
        "decided_by": "operator",
        "decided_at": now_iso,
    }
