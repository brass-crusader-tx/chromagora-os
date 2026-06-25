"""CRM-lite schemas for leads, quotes, jobs, and message drafts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Length limits — prevent abuse / accidental megastrings
_NAME = 200
_CONTACT = 120
_EMAIL = 254
_COMPANY = 200
_TITLE = 120
_NOTES = 5000
_STATUS = 50


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

class LeadBase(BaseModel):
    business_id: UUID
    customer_name: str = Field(..., max_length=_NAME)
    customer_contact: str = Field(default="", max_length=_CONTACT)
    contact_email: Optional[str] = Field(default=None, max_length=_EMAIL)
    contact_phone: Optional[str] = Field(default=None, max_length=_CONTACT)
    company_name: Optional[str] = Field(default=None, max_length=_COMPANY)
    contact_title: Optional[str] = Field(default=None, max_length=_TITLE)
    source: Optional[str] = Field(default=None, max_length=_STATUS)
    service_type: Optional[str] = Field(default=None, max_length=_STATUS)
    status: str = Field(default="new", max_length=_STATUS)
    notes: Optional[str] = Field(default=None, max_length=_NOTES)


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    customer_name: Optional[str] = Field(default=None, max_length=_NAME)
    customer_contact: Optional[str] = Field(default=None, max_length=_CONTACT)
    contact_email: Optional[str] = Field(default=None, max_length=_EMAIL)
    contact_phone: Optional[str] = Field(default=None, max_length=_CONTACT)
    company_name: Optional[str] = Field(default=None, max_length=_COMPANY)
    contact_title: Optional[str] = Field(default=None, max_length=_TITLE)
    source: Optional[str] = Field(default=None, max_length=_STATUS)
    service_type: Optional[str] = Field(default=None, max_length=_STATUS)
    status: Optional[str] = Field(default=None, max_length=_STATUS)
    notes: Optional[str] = Field(default=None, max_length=_NOTES)


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
    quote_amount: Optional[float] = Field(default=None, ge=0, le=1_000_000_000)
    service_type: str = Field(..., max_length=_STATUS)
    status: str = Field(default="draft", max_length=_STATUS)
    sent_at: Optional[datetime] = None
    last_followup_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=_NOTES)


class QuoteCreate(QuoteBase):
    pass


class QuoteUpdate(BaseModel):
    quote_amount: Optional[float] = Field(default=None, ge=0, le=1_000_000_000)
    service_type: Optional[str] = Field(default=None, max_length=_STATUS)
    status: Optional[str] = Field(default=None, max_length=_STATUS)
    sent_at: Optional[datetime] = None
    last_followup_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=_NOTES)


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
    customer_name: str = Field(..., max_length=_NAME)
    service_type: str = Field(..., max_length=_STATUS)
    status: str = Field(default="scheduled", max_length=_STATUS)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=_NOTES)


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=_STATUS)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=_NOTES)


class JobResponse(JobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Message Drafts
# ---------------------------------------------------------------------------

_DRAFT_BODY = 10_000

class MessageDraftBase(BaseModel):
    business_id: UUID
    channel: str = Field(..., max_length=50)
    recipient: str = Field(..., max_length=_EMAIL)
    subject: Optional[str] = Field(default=None, max_length=_NAME)
    body: str = Field(..., max_length=_DRAFT_BODY)
    status: str = Field(default="draft", max_length=_STATUS)
    related_action_proposal_id: Optional[UUID] = None
    related_workflow_run_id: Optional[UUID] = None


class MessageDraftCreate(MessageDraftBase):
    pass


class MessageDraftUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=_STATUS)
    body: Optional[str] = Field(default=None, max_length=_DRAFT_BODY)
    subject: Optional[str] = Field(default=None, max_length=_NAME)


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
    content: str = Field(..., max_length=_NOTES)
    job_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    note_type: str = Field(default="field_note", max_length=50)


class MobilePhotoMetadata(BaseModel):
    """POST /mobile/capture/photo-metadata body."""
    business_id: UUID
    job_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    caption: Optional[str] = Field(default=None, max_length=_NAME)
    photo_url: Optional[str] = Field(default=None, max_length=2048)
    taken_at: Optional[datetime] = None


class MobileCaptureResponse(BaseModel):
    id: UUID
    business_id: UUID
    note_type: str
    content: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
