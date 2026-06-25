"""Voice service — call records and summary management.

No telephony yet. This service manages call metadata and structured summaries.
Future: webhook from telephony provider (Telnyx, Twilio) creates CallRecord,
LLM generates CallSummary from transcript.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_schemas.voice import (
    CallRecordCreate,
    CallRecordResponse,
    CallSummaryCreate,
    CallSummaryResponse,
    VoiceQualificationResult,
)

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.base import get_supabase, get_supabase_admin
    return get_supabase()


def _table_admin(name: str):
    from chromagora_api.db.base import get_supabase_admin
    sb = get_supabase_admin()
    if not sb:
        raise RuntimeError("Database not configured")
    return sb.table(name)


def create_call_record(business_id: UUID, data: CallRecordCreate) -> Optional[CallRecordResponse]:
    """Create a call record."""
    payload = {
        "business_id": str(business_id),
        "caller_phone": data.caller_phone,
        "caller_name": data.caller_name,
        "call_status": data.call_status,
        "started_at": data.started_at.isoformat(),
        "ended_at": data.ended_at.isoformat() if data.ended_at else None,
        "recording_url": data.recording_url,
        "consent_recorded": data.consent_recorded,
        "trace_id": data.trace_id,
    }
    resp = _table_admin("call_records").insert(payload).execute()
    if not resp.data:
        return None
    return CallRecordResponse(**resp.data[0])


def get_call_record(call_record_id: UUID) -> Optional[CallRecordResponse]:
    """Get a call record by ID."""
    sb = _get_supabase()
    if not sb:
        return None

    resp = sb.table("call_records").select("*").eq("id", str(call_record_id)).execute()
    if not resp.data:
        return None
    return CallRecordResponse(**resp.data[0])


def list_call_records(business_id: UUID, limit: int = 50) -> list[CallRecordResponse]:
    """List call records for a business."""
    sb = _get_supabase()
    if not sb:
        return []

    resp = (
        sb.table("call_records")
        .select("*")
        .eq("business_id", str(business_id))
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [CallRecordResponse(**row) for row in (resp.data or [])]


def update_transcript(call_record_id: UUID, transcript_text: str) -> Optional[CallRecordResponse]:
    """Update the transcript text for a call record."""
    resp = (
        _table_admin("call_records")
        .update({"transcript_text": transcript_text, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", str(call_record_id))
        .execute()
    )
    if not resp.data:
        return None
    return CallRecordResponse(**resp.data[0])


def create_call_summary(data: CallSummaryCreate) -> Optional[CallSummaryResponse]:
    """Create a call summary."""
    payload = {
        "call_record_id": str(data.call_record_id),
        "intent": data.intent,
        "service_type": data.service_type,
        "address_or_area": data.address_or_area,
        "urgency": data.urgency,
        "lead_quality": data.lead_quality,
        "escalation_required": data.escalation_required,
        "escalation_reason": data.escalation_reason,
        "structured_notes": data.structured_notes or {},
        "confidence": data.confidence,
    }
    resp = _table_admin("call_summaries").insert(payload).execute()
    if not resp.data:
        return None
    return CallSummaryResponse(**resp.data[0])


def get_call_summary(call_record_id: UUID) -> Optional[CallSummaryResponse]:
    """Get the summary for a call record."""
    sb = _get_supabase()
    if not sb:
        return None

    resp = (
        sb.table("call_summaries")
        .select("*")
        .eq("call_record_id", str(call_record_id))
        .execute()
    )
    if not resp.data:
        return None
    return CallSummaryResponse(**resp.data[0])


def qualify_call_transcript(transcript_text: str) -> VoiceQualificationResult:
    """Deterministic voice qualification from transcript text.

    No LLM in v0.1. Uses keyword matching.
    Future: route to LLM for nuanced qualification.
    """
    text_lower = transcript_text.lower()

    # Intent detection
    intent = "unknown"
    if any(w in text_lower for w in ["estimate", "quote", "price", "cost"]):
        intent = "estimate_request"
    elif any(w in text_lower for w in ["emergency", "urgent", "asap", "right now"]):
        intent = "emergency"
    elif any(w in text_lower for w in ["schedule", "book", "appointment"]):
        intent = "booking"
    elif any(w in text_lower for w in ["cancel", "reschedule", "change"]):
        intent = "schedule_change"
    elif any(w in text_lower for w in ["question", "information", "tell me", "what"]):
        intent = "information"

    # Service type detection
    service_type = None
    keywords = {
        "lawn": "lawn_care", "mowing": "lawn_care", "mow": "lawn_care",
        "snow": "snow_removal", "plow": "snow_removal",
        "landscape": "landscaping", "garden": "landscaping",
        "roof": "roofing", "gutter": "gutter_cleaning",
        "paint": "painting", "clean": "cleaning",
        "tree": "tree_service", "trim": "tree_service",
    }
    for kw, svc in keywords.items():
        if kw in text_lower:
            service_type = svc
            break

    # Urgency
    urgency = "normal"
    if any(w in text_lower for w in ["emergency", "urgent", "asap", "flooding", "broken"]):
        urgency = "high"

    photos_requested = any(w in text_lower for w in ["photo", "picture", "send me", "show me"])
    escalation_required = intent == "emergency"
    escalation_reason = "Emergency call requires human follow-up" if escalation_required else None

    missing_information = []
    if not service_type:
        missing_information.append("service_type")
    if not any(w in text_lower for w in ["address", "location", "street", "ave", "road"]):
        missing_information.append("address_or_area")
    if not any(w in text_lower for w in ["name", "called", "this is", "i'm"]):
        missing_information.append("caller_name")
    if not any(w in text_lower for w in ["tomorrow", "monday", "next week", "morning"]):
        missing_information.append("timeline")

    next_action = "schedule_estimate"
    if intent == "emergency":
        next_action = "escalate_to_emergency_line"
    elif intent == "information":
        next_action = "send_information_packet"
    elif intent == "booking":
        next_action = "offer_available_slots"

    return VoiceQualificationResult(
        caller_intent=intent,
        service_type=service_type,
        urgency=urgency,
        photos_requested=photos_requested,
        estimate_booking_recommended=intent in ("estimate_request", "booking"),
        escalation_required=escalation_required,
        escalation_reason=escalation_reason,
        next_action=next_action,
        confidence=0.5 if service_type else 0.2,
        missing_information=missing_information,
    )
