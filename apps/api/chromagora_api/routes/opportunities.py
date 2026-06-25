"""Opportunities API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("")
async def list_opportunities(business_id: UUID | None = None):
    """List opportunities, optionally filtered by business."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    query = sb.table("opportunities").select("*").order("created_at", desc=True)
    if business_id:
        query = query.eq("business_id", str(business_id))
    resp = query.execute()
    return resp.data or []


@router.post("")
async def create_opportunity(body: dict):
    """Create a new opportunity."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    title = body.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    data = {
        "title": title,
        "description": body.get("description"),
        "stage": body.get("stage", "new"),
        "value": body.get("value"),
        "source": body.get("source"),
        "contact_name": body.get("contact_name"),
        "business_id": str(body["business_id"]) if body.get("business_id") else None,
    }
    resp = sb.table("opportunities").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create opportunity")
    return resp.data[0]
