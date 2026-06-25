"""Business listing and creation routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_tenant_id, get_backend_supabase

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("")
async def list_businesses():
    """List all businesses."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    resp = (
        sb.table("businesses")
        .select("id, legal_name, public_name, service_area_description, status, created_at")
        .eq("tenant_id", tenant_id)
        .order("created_at")
        .execute()
    )
    for row in (resp.data or []):
        row["name"] = row.get("public_name") or row.get("legal_name", "")
        row["description"] = row.get("service_area_description")
    return resp.data or []


@router.post("")
async def create_business(body: dict):
    """Create a new business."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    data = {
        "tenant_id": tenant_id,
        "legal_name": name,
        "slug": body.get("slug", name.lower().replace(" ", "-")),
        "status": body.get("status", "active"),
    }
    if body.get("description"):
        data["service_area_description"] = body["description"]
    resp = sb.table("businesses").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create business")
    return resp.data[0]


@router.get("/{business_id}")
async def get_business(business_id: str):
    """Get a single business by ID."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    resp = (
        sb.table("businesses")
        .select("*")
        .eq("id", business_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Business not found")
    row = resp.data[0]
    row["name"] = row.get("public_name") or row.get("legal_name", "")
    row["description"] = row.get("service_area_description")
    return row
