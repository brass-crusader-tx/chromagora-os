"""Approval Inbox API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
async def list_approvals(status: str = "pending"):
    """List approval requests, filtered by status."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    query = (
        sb.table("approval_requests")
        .select("*, action_proposals(*)")
    )
    if status:
        query = query.eq("status", status)

    resp = query.execute()
    return resp.data or []


@router.post("/{approval_id}/approve")
async def approve_request(approval_id: UUID, decision_notes: str = ""):
    """Approve an approval request."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    resp = (
        sb.table("approval_requests")
        .update({
            "status": "approved",
            "decided_by": "operator",
            "decided_at": "now()",
            "decision_notes": decision_notes,
        })
        .eq("id", str(approval_id))
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
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    resp = (
        sb.table("approval_requests")
        .update({
            "status": "rejected",
            "decided_by": "operator",
            "decided_at": "now()",
            "decision_notes": decision_notes,
        })
        .eq("id", str(approval_id))
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
