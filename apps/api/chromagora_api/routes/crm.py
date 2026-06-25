"""CRM-lite routes — leads, quotes, jobs, message drafts."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.services.crm_service import (
    create_lead, get_lead, list_leads, update_lead,
    create_quote, get_quote, list_quotes, update_quote,
    create_job, get_job, list_jobs, update_job,
    create_message_draft, get_message_draft, list_message_drafts, update_message_draft,
)
from chromagora_schemas.crm import (
    LeadCreate, LeadUpdate,
    QuoteCreate, QuoteUpdate,
    JobCreate, JobUpdate,
    MessageDraftCreate, MessageDraftUpdate,
)

router = APIRouter(prefix="/crm", tags=["crm"])


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

@router.post("/leads", status_code=status.HTTP_201_CREATED)
async def create_lead_endpoint(data: LeadCreate):
    result = create_lead(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create lead")
    return result


@router.get("/leads/{lead_id}")
async def get_lead_endpoint(lead_id: UUID):
    result = get_lead(lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result


@router.get("/leads")
async def list_leads_endpoint(business_id: UUID, status: str | None = None):
    return list_leads(business_id, status)


@router.patch("/leads/{lead_id}")
async def update_lead_endpoint(lead_id: UUID, data: LeadUpdate):
    result = update_lead(lead_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

@router.post("/quotes", status_code=status.HTTP_201_CREATED)
async def create_quote_endpoint(data: QuoteCreate):
    result = create_quote(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create quote")
    return result


@router.get("/quotes/{quote_id}")
async def get_quote_endpoint(quote_id: UUID):
    result = get_quote(quote_id)
    if not result:
        raise HTTPException(status_code=404, detail="Quote not found")
    return result


@router.get("/quotes")
async def list_quotes_endpoint(business_id: UUID, status: str | None = None):
    return list_quotes(business_id, status)


@router.patch("/quotes/{quote_id}")
async def update_quote_endpoint(quote_id: UUID, data: QuoteUpdate):
    result = update_quote(quote_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Quote not found")
    return result


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job_endpoint(data: JobCreate):
    result = create_job(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create job")
    return result


@router.get("/jobs/{job_id}")
async def get_job_endpoint(job_id: UUID):
    result = get_job(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.get("/jobs")
async def list_jobs_endpoint(business_id: UUID, status: str | None = None):
    return list_jobs(business_id, status)


@router.patch("/jobs/{job_id}")
async def update_job_endpoint(job_id: UUID, data: JobUpdate):
    result = update_job(job_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


# ---------------------------------------------------------------------------
# Message Drafts
# ---------------------------------------------------------------------------

@router.post("/message-drafts", status_code=status.HTTP_201_CREATED)
async def create_message_draft_endpoint(data: MessageDraftCreate):
    result = create_message_draft(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create message draft")
    return result


@router.get("/message-drafts/{draft_id}")
async def get_message_draft_endpoint(draft_id: UUID):
    result = get_message_draft(draft_id)
    if not result:
        raise HTTPException(status_code=404, detail="Message draft not found")
    return result


@router.get("/message-drafts")
async def list_message_drafts_endpoint(business_id: UUID, status: str | None = None):
    return list_message_drafts(business_id, status)


@router.patch("/message-drafts/{draft_id}")
async def update_message_draft_endpoint(draft_id: UUID, data: MessageDraftUpdate):
    result = update_message_draft(draft_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Message draft not found")
    return result


# ---------------------------------------------------------------------------
# Contacts (alias for leads)
# ---------------------------------------------------------------------------

@router.get("/contacts")
async def list_contacts_endpoint(business_id: UUID, status: str | None = None):
    """List contacts (alias for leads)."""
    return list_leads(business_id, status)


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact_endpoint(data: LeadCreate):
    """Create a contact (alias for creating a lead)."""
    result = create_lead(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create contact")
    return result
