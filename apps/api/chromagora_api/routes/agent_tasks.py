"""Agent task execution endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase
from chromagora_api.services.reputation_agent import run_review_request
from chromagora_api.services.sales_agent import run_stale_quote_followup

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/reputation/run-review-request-dry-run")
async def reputation_review_request(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
):
    """Execute the Reputation Agent review request workflow (dry-run)."""
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
