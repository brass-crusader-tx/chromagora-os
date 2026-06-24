"""Business listing route."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("")
async def list_businesses():
    """List all businesses."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = sb.table("businesses").select("id, name, created_at").execute()
    return resp.data or []


@router.get("/{business_id}")
async def get_business(business_id: str):
    """Get a single business by ID."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("businesses")
        .select("*")
        .eq("id", business_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Business not found")
    return resp.data[0]
