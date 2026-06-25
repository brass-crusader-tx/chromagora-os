"""Workflow API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase
from chromagora_api.services.workflows import (
    run_review_request_workflow,
    run_stale_quote_followup_workflow,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
async def list_workflow_definitions():
    """List all workflow definitions."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = sb.table("workflow_definitions").select("*").order("created_at", desc=True).execute()
    return resp.data or []


@router.post("")
async def create_workflow_definition(body: dict):
    """Create a new workflow definition."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    data = {
        "name": name,
        "description": body.get("description"),
        "status": body.get("status", "draft"),
        "definition": body.get("definition", {}),
    }
    resp = sb.table("workflow_definitions").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create workflow definition")
    return resp.data[0]


@router.post("/review-request/dry-run")
async def review_request_dry_run(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
):
    """Execute the completed-job review-request workflow in dry-run mode."""
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
    result = run_review_request_workflow(
        tenant_id=tenant_id,
        business_id=business_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        job_summary=job_summary,
        completed_at=completed_at,
    )
    return result


@router.post("/stale-quote-followup/dry-run")
async def stale_quote_followup_dry_run(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    service_type: str,
    quote_sent_at: str,
    quote_id: str | None = None,
    quote_amount: float | None = None,
    last_contact_at: str | None = None,
):
    """Execute the stale-quote follow-up workflow in dry-run mode."""
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
    result = run_stale_quote_followup_workflow(
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
