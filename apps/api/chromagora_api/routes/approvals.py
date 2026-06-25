"""Approval Inbox API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_tenant_id, get_backend_supabase

router = APIRouter(prefix="/approvals", tags=["approvals"])


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
    return resp.data or []


@router.post("/{approval_id}/approve")
async def approve_request(approval_id: UUID, decision_notes: str = ""):
    """Approve an approval request."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    resp = (
        sb.table("approval_requests")
        .update({
            "status": "approved",
            "decided_by": "operator",
            "decided_at": "now()",
            "decision_notes": decision_notes,
        })
        .eq("id", str(approval_id))
        .eq("tenant_id", tenant_id)
        .eq("status", "pending")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Approval request not found or already decided")

    # Emit event
    sb.table("events").insert({
        "tenant_id": resp.data[0]["tenant_id"],
        "business_id": resp.data[0].get("business_id"),
        "event_type": "action.approved",
        "source_type": "operator",
        "source_id": None,
        "payload_json": {"approval_id": str(approval_id), "decision": "approved"},
    }).execute()

    return resp.data[0]


@router.post("/{approval_id}/reject")
async def reject_request(approval_id: UUID, decision_notes: str = ""):
    """Reject an approval request."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    resp = (
        sb.table("approval_requests")
        .update({
            "status": "rejected",
            "decided_by": "operator",
            "decided_at": "now()",
            "decision_notes": decision_notes,
        })
        .eq("id", str(approval_id))
        .eq("tenant_id", tenant_id)
        .eq("status", "pending")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Approval request not found or already decided")

    # Emit event
    sb.table("events").insert({
        "tenant_id": resp.data[0]["tenant_id"],
        "business_id": resp.data[0].get("business_id"),
        "event_type": "action.rejected",
        "source_type": "operator",
        "source_id": None,
        "payload_json": {"approval_id": str(approval_id), "decision": "rejected"},
    }).execute()

    return resp.data[0]
