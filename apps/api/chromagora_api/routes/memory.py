"""Memory Artifacts API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chromagora_api.db.base import get_supabase
from chromagora_api.services.vector_memory import list_artifacts as vm_list_artifacts

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/artifacts")
async def list_memory_artifacts(business_id: UUID | None = None):
    """List memory artifacts, optionally filtered by business."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        artifacts = vm_list_artifacts(str(business_id) if business_id else None)
        return artifacts
    except Exception:
        # Fallback: direct query if vector_memory service fails
        query = sb.table("memory_artifacts").select("*").order("created_at", desc=True)
        if business_id:
            query = query.eq("business_id", str(business_id))
        resp = query.execute()
        return resp.data or []
