"""Procurement Scout API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_backend_supabase, get_business_tenant_id
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
    try:
        sb = get_backend_supabase()
        tenant_id_raw = get_business_tenant_id(str(business_id), sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not tenant_id_raw:
        raise HTTPException(status_code=404, detail="Business not found")

    tenant_id = UUID(tenant_id_raw)
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
