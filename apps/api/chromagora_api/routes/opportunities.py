"""Opportunities API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import (
    DatabaseUnavailable,
    TenantError,
    get_active_business_ids,
    get_active_tenant_id,
    get_backend_supabase,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("")
async def list_opportunities(business_id: UUID | None = None):
    """List opportunities, optionally filtered by business."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
        active_business_ids = get_active_business_ids(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    query = sb.table("opportunities").select("*").eq("tenant_id", tenant_id).order("created_at", desc=True)
    if business_id:
        if str(business_id) not in active_business_ids:
            raise HTTPException(status_code=404, detail="Business not found")
        query = query.eq("business_id", str(business_id))
    resp = query.execute()
    for row in (resp.data or []):
        row["value"] = row.get("estimated_value_max") or row.get("estimated_value_min")
        # Map status: DB uses 'detected' etc, frontend uses 'new' etc
        status_map = {"detected": "new", "qualifying": "qualified", "qualified": "qualified", "rejected": "lost"}
        row["status"] = status_map.get(row.get("status", ""), row.get("status", ""))
        # Ensure created_at is present
        if "created_at" not in row:
            row["published_at"] = row.get("published_at", "")
        row["stage"] = row["status"]
        row["source"] = row.get("source_name")
    return resp.data or []


@router.post("")
async def create_opportunity(body: dict):
    """Create a new opportunity."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
        active_business_ids = get_active_business_ids(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    title = body.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    business_id = str(body["business_id"]) if body.get("business_id") else (
        active_business_ids[0] if active_business_ids else None
    )
    if not business_id or business_id not in active_business_ids:
        raise HTTPException(status_code=404, detail="Business not found")
    data = {
        "tenant_id": tenant_id,
        "business_id": business_id,
        "title": title,
        "description": body.get("description"),
        "source_name": body.get("source") or body.get("contact_name") or "manual",
        "opportunity_type": body.get("opportunity_type", "custom"),
        "estimated_value_min": body.get("estimated_value_min") or body.get("value"),
        "estimated_value_max": body.get("estimated_value_max") or body.get("value"),
        "status": "detected",
    }
    resp = sb.table("opportunities").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create opportunity")
    return resp.data[0]
