"""Business listing and creation routes."""

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
    resp = sb.table("businesses").select("id, legal_name, created_at").execute()
    return resp.data or []


@router.post("")
async def create_business(body: dict):
    """Create a new business."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    data = {
        "name": name,
        "slug": body.get("slug", name.lower().replace(" ", "-")),
        "status": body.get("status", "active"),
    }
    resp = sb.table("businesses").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create business")
    return resp.data[0]


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
