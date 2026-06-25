"""CRM-lite schemas for leads, quotes, jobs, and message drafts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

class LeadBase(BaseModel):
    business_id: UUID
    customer_name: str
    customer_contact: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    contact_title: Optional[str] = None
    source: Optional[str] = None
    service_type: Optional[str] = None
    status: str = "new"
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    contact_title: Optional[str] = None
    source: Optional[str] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

class QuoteBase(BaseModel):
    business_id: UUID
    lead_id: Optional[UUID] = None
    quote_amount: Optional[float] = None
    service_type: str
    status: str = "draft"
    sent_at: Optional[datetime] = None
    last_followup_at: Optional[datetime] = None
    notes: Optional[str] = None


class QuoteCreate(QuoteBase):
    pass


class QuoteUpdate(BaseModel):
    quote_amount: Optional[float] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    sent_at: Optional[datetime] = None
    last_followup_at: Optional[datetime] = None
    notes: Optional[str] = None


class QuoteResponse(QuoteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

class JobBase(BaseModel):
    business_id: UUID
    lead_id: Optional[UUID] = None
    quote_id: Optional[UUID] = None
    customer_name: str
    service_type: str
    status: str = "scheduled"
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class JobResponse(JobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Message Drafts
# ---------------------------------------------------------------------------

class MessageDraftBase(BaseModel):
    business_id: UUID
    channel: str
    recipient: str
    subject: Optional[str] = None
    body: str
    status: str = "draft"
    related_action_proposal_id: Optional[UUID] = None
    related_workflow_run_id: Optional[UUID] = None


class MessageDraftCreate(MessageDraftBase):
    pass


class MessageDraftUpdate(BaseModel):
    status: Optional[str] = None
    body: Optional[str] = None
    subject: Optional[str] = None


class MessageDraftResponse(MessageDraftBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Mobile — capture payloads
# ---------------------------------------------------------------------------

class MobileNoteCapture(BaseModel):
    """POST /mobile/capture/note body."""
    business_id: UUID
    content: str
    job_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    note_type: str = "field_note"


class MobilePhotoMetadata(BaseModel):
    """POST /mobile/capture/photo-metadata body."""
    business_id: UUID
    job_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    caption: Optional[str] = None
    photo_url: Optional[str] = None
    taken_at: Optional[datetime] = None


class MobileCaptureResponse(BaseModel):
    id: UUID
    business_id: UUID
    note_type: str
    content: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
