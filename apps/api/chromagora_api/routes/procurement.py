"""Procurement Scout API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase
from chromagora_api.services.procurement_agent import evaluate_opportunity

router = APIRouter(prefix="/agents/procurement", tags=["agents"])


@router.post("/evaluate-opportunity-dry-run")
async def procurement_evaluate(
    business_id: UUID,
    opportunity_type: str,
    source_name: str,
    title: str,
    description: str = "",
    source_url: str | None = None,
    location: str | None = None,
    deadline_at: str | None = None,
    estimated_value_min: float | None = None,
    estimated_value_max: float | None = None,
    service_type: str = "",
):
    """Evaluate a procurement opportunity (dry-run)."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    biz_resp = (
        sb.table("businesses")
        .select("tenant_id")
        .eq("id", str(business_id))
        .execute()
    )
    if not biz_resp.data:
        raise HTTPException(status_code=404, detail="Business not found")

    tenant_id = UUID(biz_resp.data[0]["tenant_id"])
    result = evaluate_opportunity(
        tenant_id=tenant_id,
        business_id=business_id,
        opportunity_type=opportunity_type,
        source_name=source_name,
        title=title,
        description=description,
        source_url=source_url,
        location=location,
        deadline_at=deadline_at,
        estimated_value_min=estimated_value_min,
        estimated_value_max=estimated_value_max,
        service_type=service_type,
    )
    return result
