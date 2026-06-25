"""Action Ledger API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chromagora_api.db.base import get_supabase

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("")
async def list_ledger(business_id: UUID | None = None, agent_id: UUID | None = None):
    """List ledger entries, optionally filtered by business or agent."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    query = sb.table("action_executions").select("*").order("started_at", desc=True)
    if business_id:
        query = query.eq("business_id", str(business_id))
    if agent_id:
        query = query.eq("agent_id", str(agent_id))
    resp = query.execute()
    return resp.data or []
