"""Tests for voice schema validation (Chapter 23)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from chromagora_schemas.voice import (
    CallRecordCreate,
    CallRecordResponse,
    CallSummaryCreate,
    CallSummaryResponse,
    VoiceQualificationResult,
)


def test_call_record_create():
    data = CallRecordCreate(
        business_id=uuid4(),
        caller_phone="+15551234567",
        caller_name="John",
        call_status="inbound",
        started_at=datetime.now(timezone.utc),
    )
    assert data.caller_phone == "+15551234567"
    assert data.call_status == "inbound"


def test_call_record_create_defaults():
    data = CallRecordCreate(
        business_id=uuid4(),
        caller_phone="+15551234567",
        started_at=datetime.now(timezone.utc),
    )
    assert data.call_status == "inbound"
    assert data.consent_recorded is False


def test_call_record_response():
    data = CallRecordResponse(
        id=uuid4(),
        business_id=uuid4(),
        caller_phone="+15551234567",
        call_status="inbound",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert data.id is not None


def test_call_summary_create():
    data = CallSummaryCreate(
        call_record_id=uuid4(),
        intent="estimate_request",
        urgency="normal",
        lead_quality="warm",
        escalation_required=False,
        confidence=0.8,
    )
    assert data.intent == "estimate_request"
    assert data.urgency == "normal"


def test_call_summary_defaults():
    data = CallSummaryCreate(
        call_record_id=uuid4(),
    )
    assert data.intent == "unknown"
    assert data.urgency == "normal"
    assert data.escalation_required is False
    assert data.confidence == 0.0


def test_voice_qualification_result():
    data = VoiceQualificationResult(
        caller_intent="estimate_request",
        service_type="lawn_care",
        urgency="high",
        escalation_required=False,
        confidence=0.7,
    )
    assert data.caller_intent == "estimate_request"
    assert data.estimate_booking_recommended is False


def test_voice_qualification_defaults():
    data = VoiceQualificationResult()
    assert data.caller_intent == "unknown"
    assert data.urgency == "normal"
    assert data.bad_fit_signals == []
    assert data.missing_information == []
