"""Action Ledger API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chromagora_api.db.tenant import get_active_tenant_id, get_backend_supabase

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("")
async def list_ledger(business_id: UUID | None = None, agent_id: UUID | None = None):
    """List ledger entries, optionally filtered by business or agent."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    query = (
        sb.table("action_executions")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("started_at", desc=True)
    )
    if business_id:
        query = query.eq("business_id", str(business_id))
    if agent_id:
        query = query.eq("executed_by_id", str(agent_id))
    resp = query.execute()
    for row in (resp.data or []):
        row["action"] = row.get("tool_action") or row.get("tool_name", "")
        row["actor"] = row.get("executed_by_type", "")
        row["status"] = row.get("result_status", "")
        row["created_at"] = row.get("started_at", "")
        row.setdefault("dollar_impact", None)
    return resp.data or []
