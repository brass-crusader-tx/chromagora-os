"""Runtime simulation endpoints.

These `/demo/*` routes are retained for backward compatibility with the
original operator walkthrough. They simulate internal OS runtime loops; they
are not prospect demo-site or Demo Factory endpoints.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_backend_supabase, get_business_tenant_id
from chromagora_api.services.reputation_agent import run_review_request
from chromagora_api.services.sales_agent import run_stale_quote_followup
from chromagora_api.services.procurement_agent import evaluate_opportunity

router = APIRouter(
    prefix="/demo",
    tags=["runtime simulations"],
    responses={
        200: {
            "description": "Internal runtime simulation result. Future prospect demo-site APIs should use /demo-sites/* or /demo-site-batches/*.",
        }
    },
)


class ReviewRequestSimInput(BaseModel):
    business_id: UUID
    customer_name: str
    customer_contact: str
    job_summary: str
    completed_at: str


class StaleQuoteSimInput(BaseModel):
    business_id: UUID
    customer_name: str
    customer_contact: str
    service_type: str
    quote_sent_at: str
    quote_amount: float | None = None
    quote_id: str | None = None
    last_contact_at: str | None = None


class OpportunitySimInput(BaseModel):
    business_id: UUID
    opportunity_type: str
    source_name: str
    title: str
    description: str = ""
    source_url: str | None = None
    location: str | None = None
    deadline_at: str | None = None
    estimated_value_min: float | None = None
    estimated_value_max: float | None = None
    service_type: str = ""


def get_supabase():
    """Compatibility seam for tests and internal callers."""
    return get_backend_supabase()


def _scoped_business_context(business_id: UUID):
    try:
        sb = get_supabase()
        if not sb:
            raise DatabaseUnavailable("Database not configured")
        tenant_id = get_business_tenant_id(str(business_id), sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Business not found")
    return sb, UUID(tenant_id)


@router.post("/review-request-simulation")
async def review_request_simulation(data: ReviewRequestSimInput):
    """Run the full review request simulation."""
    sb, tenant_id = _scoped_business_context(data.business_id)

    # Step 1: Emit job.completed event
    event_resp = sb.table("events").insert({
        "tenant_id": str(tenant_id),
        "business_id": str(data.business_id),
        "event_type": "job.completed",
        "source_type": "demo",
        "payload_json": {
            "customer_name": data.customer_name,
            "job_summary": data.job_summary,
            "completed_at": data.completed_at,
        },
    }).execute()
    event_id = event_resp.data[0]["id"] if event_resp.data else None

    # Step 2-7: Run Reputation Agent
    agent_result = run_review_request(
        tenant_id=tenant_id,
        business_id=data.business_id,
        customer_name=data.customer_name,
        customer_contact=data.customer_contact,
        job_summary=data.job_summary,
        completed_at=data.completed_at,
    )

    return {
        "status": "completed",
        "event_id": event_id,
        "agent_result": agent_result,
    }


@router.post("/stale-quote-simulation")
async def stale_quote_simulation(data: StaleQuoteSimInput):
    """Run the full stale quote simulation."""
    sb, tenant_id = _scoped_business_context(data.business_id)

    # Step 1: Emit event
    event_resp = sb.table("events").insert({
        "tenant_id": str(tenant_id),
        "business_id": str(data.business_id),
        "event_type": "quote.stale",
        "source_type": "demo",
        "payload_json": {
            "customer_name": data.customer_name,
            "service_type": data.service_type,
            "quote_sent_at": data.quote_sent_at,
        },
    }).execute()
    event_id = event_resp.data[0]["id"] if event_resp.data else None

    # Step 2-4: Run Sales Agent
    agent_result = run_stale_quote_followup(
        tenant_id=tenant_id,
        business_id=data.business_id,
        customer_name=data.customer_name,
        customer_contact=data.customer_contact,
        service_type=data.service_type,
        quote_sent_at=data.quote_sent_at,
        quote_id=data.quote_id,
        quote_amount=data.quote_amount,
        last_contact_at=data.last_contact_at,
    )

    return {
        "status": "completed",
        "event_id": event_id,
        "agent_result": agent_result,
    }


@router.post("/opportunity-simulation")
async def opportunity_simulation(data: OpportunitySimInput):
    """Run the full opportunity simulation."""
    sb, tenant_id = _scoped_business_context(data.business_id)

    # Step 1: Emit event
    event_resp = sb.table("events").insert({
        "tenant_id": str(tenant_id),
        "business_id": str(data.business_id),
        "event_type": "opportunity.detected",
        "source_type": "demo",
        "payload_json": {
            "opportunity_type": data.opportunity_type,
            "source_name": data.source_name,
            "title": data.title,
        },
    }).execute()
    event_id = event_resp.data[0]["id"] if event_resp.data else None

    # Step 2-5: Run Procurement Scout
    agent_result = evaluate_opportunity(
        tenant_id=tenant_id,
        business_id=data.business_id,
        opportunity_type=data.opportunity_type,
        source_name=data.source_name,
        title=data.title,
        description=data.description,
        source_url=data.source_url,
        location=data.location,
        deadline_at=data.deadline_at,
        estimated_value_min=data.estimated_value_min,
        estimated_value_max=data.estimated_value_max,
        service_type=data.service_type,
    )

    return {
        "status": "completed",
        "event_id": event_id,
        "agent_result": agent_result,
    }
