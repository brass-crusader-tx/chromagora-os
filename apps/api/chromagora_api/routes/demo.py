"""Demo simulation endpoints — end-to-end loops."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase
from chromagora_api.services.reputation_agent import run_review_request
from chromagora_api.services.sales_agent import run_stale_quote_followup
from chromagora_api.services.procurement_agent import evaluate_opportunity

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/review-request-simulation")
async def review_request_simulation(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
):
    """Run the full review request simulation.

    1. Emit job.completed event
    2. Trigger Reputation Agent v0
    3. Build ContextPacket
    4. Create ActionProposal
    5. Evaluate Policy Kernel
    6. Tool Broker
    7. ApprovalRequest or dry-run ActionExecution
    8. Return all IDs
    """
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

    # Step 1: Emit job.completed event
    event_resp = sb.table("events").insert({
        "tenant_id": str(tenant_id),
        "business_id": str(business_id),
        "event_type": "job.completed",
        "source_type": "demo",
        "payload_json": {
            "customer_name": customer_name,
            "job_summary": job_summary,
            "completed_at": completed_at,
        },
    }).execute()
    event_id = event_resp.data[0]["id"] if event_resp.data else None

    # Step 2-7: Run Reputation Agent
    agent_result = run_review_request(
        tenant_id=tenant_id,
        business_id=business_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        job_summary=job_summary,
        completed_at=completed_at,
    )

    return {
        "status": "completed",
        "event_id": event_id,
        "agent_result": agent_result,
    }


@router.post("/stale-quote-simulation")
async def stale_quote_simulation(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    service_type: str,
    quote_sent_at: str,
    quote_amount: float | None = None,
    quote_id: str | None = None,
    last_contact_at: str | None = None,
):
    """Run the full stale quote simulation.

    1. Emit quote.sent or quote.stale
    2. Sales Agent v0
    3. ContextPacket, ActionProposal, Policy, Tool Broker
    4. Return all IDs
    """
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

    # Step 1: Emit event
    event_resp = sb.table("events").insert({
        "tenant_id": str(tenant_id),
        "business_id": str(business_id),
        "event_type": "quote.stale",
        "source_type": "demo",
        "payload_json": {
            "customer_name": customer_name,
            "service_type": service_type,
            "quote_sent_at": quote_sent_at,
        },
    }).execute()
    event_id = event_resp.data[0]["id"] if event_resp.data else None

    # Step 2-4: Run Sales Agent
    agent_result = run_stale_quote_followup(
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

    return {
        "status": "completed",
        "event_id": event_id,
        "agent_result": agent_result,
    }


@router.post("/opportunity-simulation")
async def opportunity_simulation(
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
    """Run the full opportunity simulation.

    1. Emit opportunity.detected
    2. Procurement Scout v0
    3. Create Opportunity, score, propose
    4. Policy, Tool Broker
    5. Return all IDs
    """
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

    # Step 1: Emit event
    event_resp = sb.table("events").insert({
        "tenant_id": str(tenant_id),
        "business_id": str(business_id),
        "event_type": "opportunity.detected",
        "source_type": "demo",
        "payload_json": {
            "opportunity_type": opportunity_type,
            "source_name": source_name,
            "title": title,
        },
    }).execute()
    event_id = event_resp.data[0]["id"] if event_resp.data else None

    # Step 2-5: Run Procurement Scout
    agent_result = evaluate_opportunity(
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

    return {
        "status": "completed",
        "event_id": event_id,
        "agent_result": agent_result,
    }
