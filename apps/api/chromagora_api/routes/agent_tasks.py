"""Agent task execution endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import get_backend_supabase, get_business_tenant_id
from chromagora_api.services.reputation_agent import run_review_request
from chromagora_api.services.sales_agent import run_stale_quote_followup

router = APIRouter(prefix="/agents", tags=["agents"])


def _tenant_for_business(business_id: UUID) -> UUID:
    try:
        sb = get_backend_supabase()
        tenant_id = get_business_tenant_id(str(business_id), sb)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Business not found")
    return UUID(tenant_id)


@router.post("/reputation/run-review-request-dry-run")
async def reputation_review_request(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
):
    """Execute the Reputation Agent review request workflow (dry-run)."""
    tenant_id = _tenant_for_business(business_id)
    result = run_review_request(
        tenant_id=tenant_id,
        business_id=business_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        job_summary=job_summary,
        completed_at=completed_at,
    )
    return result


@router.post("/sales/run-stale-quote-dry-run")
async def sales_stale_quote(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    service_type: str,
    quote_sent_at: str,
    quote_id: str | None = None,
    quote_amount: float | None = None,
    last_contact_at: str | None = None,
):
    """Execute the Sales Agent stale quote follow-up workflow (dry-run)."""
    tenant_id = _tenant_for_business(business_id)
    result = run_stale_quote_followup(
        tenant_id=tenant_id,
        business_id=business_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        service_type=service_type,
        quote_sent_at=quote_sent_at,
        quote_id=quote_id,
        quote_amount=quote_amount,
        last_contact_at=last_contact_at,
    )
    return result
