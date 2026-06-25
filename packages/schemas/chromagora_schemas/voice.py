"""Voice agent schemas — call records, summaries, and qualification.

Chapter 23 — Voice Agent Preparation.
No telephony yet. Models for future voice integration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Call Records
# ---------------------------------------------------------------------------

class CallRecordBase(BaseModel):
    business_id: UUID
    caller_phone: str
    caller_name: Optional[str] = None
    call_status: str = "inbound"
    started_at: datetime
    ended_at: Optional[datetime] = None
    recording_url: Optional[str] = None
    transcript_text: Optional[str] = None
    consent_recorded: bool = False


class CallRecordCreate(CallRecordBase):
    pass


class CallRecordResponse(CallRecordBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Call Summaries
# ---------------------------------------------------------------------------

class CallSummaryBase(BaseModel):
    call_record_id: UUID
    intent: str = "unknown"
    service_type: Optional[str] = None
    address_or_area: Optional[str] = None
    urgency: str = "normal"
    lead_quality: str = "unknown"
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    structured_notes: Optional[dict] = None
    confidence: float = 0.0


class CallSummaryCreate(CallSummaryBase):
    pass


class CallSummaryResponse(CallSummaryBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Voice Qualification Result
# ---------------------------------------------------------------------------

class VoiceQualificationResult(BaseModel):
    """Structured output from voice qualification (future LLM or deterministic)."""
    caller_intent: str = "unknown"
    service_type: Optional[str] = None
    address_or_area: Optional[str] = None
    timeline: str = "unknown"
    urgency: str = "normal"
    budget_signal: Optional[str] = None
    photos_requested: bool = False
    estimate_booking_recommended: bool = False
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    bad_fit_signals: list[str] = Field(default_factory=list)
    next_action: str = "none"
    confidence: float = 0.0
    missing_information: list[str] = Field(default_factory=list)
