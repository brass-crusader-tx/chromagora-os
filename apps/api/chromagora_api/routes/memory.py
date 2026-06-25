"""Memory Artifacts API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_business_ids, get_backend_supabase
from chromagora_api.services.vector_memory import list_artifacts as vm_list_artifacts

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/artifacts")
async def list_memory_artifacts(business_id: UUID | None = None):
    """List memory artifacts, optionally filtered by business."""
    try:
        sb = get_backend_supabase()
        active_business_ids = get_active_business_ids(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if business_id and str(business_id) not in active_business_ids:
        raise HTTPException(status_code=404, detail="Business not found")
    if not active_business_ids:
        return []
    try:
        artifacts = vm_list_artifacts(str(business_id) if business_id else None)
        if business_id:
            scoped = artifacts
        else:
            scoped = [row for row in artifacts if row.get("business_id") in active_business_ids]
    except Exception:
        # Fallback: direct query if vector_memory service fails
        query = sb.table("memory_artifacts").select("*").order("created_at", desc=True)
        if business_id:
            query = query.eq("business_id", str(business_id))
        else:
            query = query.in_("business_id", active_business_ids)
        resp = query.execute()
        scoped = resp.data or []
    for row in scoped:
        row["name"] = row.get("title", "")
        row["content"] = row.get("text_content", "")
        row["source"] = row.get("source_ref")
    return scoped
