"""CRM-lite routes — leads, quotes, jobs, message drafts."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_business_ids, get_backend_supabase
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


def _resolve_business_id(business_id: UUID | None = None) -> UUID:
    active_business_ids = _active_business_ids()
    if business_id:
        if str(business_id) not in active_business_ids:
            raise HTTPException(status_code=404, detail="Business not found")
        return business_id
    if not active_business_ids:
        raise HTTPException(status_code=404, detail="Business not found")
    return UUID(active_business_ids[0])


def _active_business_ids() -> list[str]:
    try:
        sb = get_backend_supabase()
        return get_active_business_ids(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


def _contact_from_lead(row: dict) -> dict:
    contact_email = row.get("contact_email")
    contact_phone = row.get("contact_phone")
    company = row.get("company_name")
    title = row.get("contact_title")
    metadata = _contact_metadata_from_notes(row.get("notes"))
    contact_email = contact_email or metadata.get("email")
    contact_phone = contact_phone or metadata.get("phone")
    company = company or metadata.get("company")
    title = title or metadata.get("title")
    fallback_contact = row.get("customer_contact")
    if not contact_email and isinstance(fallback_contact, str) and "@" in fallback_contact:
        contact_email = fallback_contact
    if not contact_phone and isinstance(fallback_contact, str) and "@" not in fallback_contact:
        contact_phone = fallback_contact
    return {
        "id": row["id"],
        "name": row.get("customer_name", ""),
        "email": contact_email,
        "phone": contact_phone,
        "company": company,
        "title": title,
        "status": row.get("status", "new"),
        "source": row.get("source"),
        "service_type": row.get("service_type"),
        "notes": row.get("notes"),
        "created_at": row.get("created_at", ""),
        "business_id": row.get("business_id"),
    }


def _contact_metadata_from_notes(notes: str | None) -> dict:
    if not notes or "[contact_metadata]" not in notes:
        return {}
    try:
        raw = notes.split("[contact_metadata]", 1)[1].strip().splitlines()[0]
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


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
async def list_contacts_endpoint(business_id: UUID | None = None, status: str | None = None):
    """List contacts (alias for leads). Maps DB fields to frontend-friendly names."""
    if business_id:
        leads = list_leads(_resolve_business_id(business_id), status)
    else:
        leads = []
        for bid in _active_business_ids():
            leads.extend(list_leads(UUID(bid), status))
    return [_contact_from_lead(row) for row in leads]


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact_endpoint(data: dict):
    """Create a contact (alias for creating a lead)."""
    name = data.get("name") or data.get("customer_name")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    business_id = _resolve_business_id(
        UUID(data["business_id"]) if data.get("business_id") else None
    )
    email = data.get("email") or data.get("contact_email")
    phone = data.get("phone") or data.get("contact_phone")
    lead = LeadCreate(
        business_id=business_id,
        customer_name=name,
        customer_contact=email or phone or "",
        contact_email=email,
        contact_phone=phone,
        company_name=data.get("company") or data.get("company_name"),
        contact_title=data.get("title") or data.get("contact_title"),
        source=data.get("source") or "manual",
        service_type=data.get("service_type"),
        status=data.get("status", "new"),
        notes=data.get("notes"),
    )
    result = create_lead(lead)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create contact")
    return _contact_from_lead(result)
