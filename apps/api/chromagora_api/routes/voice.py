"""Voice agent routes — call records and summaries.

Chapter 23 — Voice Agent Preparation.
No telephony integration yet. API surface for future webhook integration.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_business_ids, get_backend_supabase
from chromagora_schemas.voice import (
    CallRecordCreate,
    CallRecordResponse,
    CallSummaryCreate,
    CallSummaryResponse,
    VoiceQualificationResult,
)
from chromagora_api.services.voice_service import (
    create_call_record,
    get_call_record,
    list_call_records,
    update_transcript,
    create_call_summary,
    get_call_summary,
    qualify_call_transcript,
)

router = APIRouter(prefix="/voice", tags=["voice"])


# ---------------------------------------------------------------------------
# Call Records
# ---------------------------------------------------------------------------

@router.post("/calls", status_code=status.HTTP_201_CREATED)
async def create_call(data: CallRecordCreate):
    """Create a call record (future: triggered by telephony webhook)."""
    try:
        result = create_call_record(data.business_id, data)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create call record")
        return result
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/calls/{call_id}", response_model=CallRecordResponse)
async def get_call(call_id: UUID):
    """Get a call record by ID."""
    result = get_call_record(call_id)
    if not result:
        raise HTTPException(status_code=404, detail="Call record not found")
    return result


@router.get("/list")
async def list_all_calls(business_id: UUID = None, limit: int = 50):
    """List all call records (optionally filtered by business). Maps DB fields to frontend-friendly names."""
    try:
        sb = get_backend_supabase()
        active_business_ids = get_active_business_ids(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if business_id:
        if str(business_id) not in active_business_ids:
            raise HTTPException(status_code=404, detail="Business not found")
        active_business_ids = [str(business_id)]
    if not active_business_ids:
        return []
    query = sb.table("call_records").select("*").order("started_at", desc=True).limit(limit)
    query = query.in_("business_id", active_business_ids)
    resp = query.execute()
    results = []
    for row in (resp.data or []):
        started = row.get("started_at")
        ended = row.get("ended_at")
        duration = None
        if started and ended:
            from datetime import datetime
            try:
                s = datetime.fromisoformat(started.replace("z", "+00:00"))
                e = datetime.fromisoformat(ended.replace("z", "+00:00"))
                duration = int((e - s).total_seconds())
            except Exception:
                pass
        results.append({
            "id": row["id"],
            "caller_number": row.get("caller_phone", ""),
            "recipient_number": None,
            "direction": row.get("call_status", ""),
            "status": row.get("call_status", ""),
            "duration_seconds": duration,
            "created_at": row.get("created_at", started or ""),
            "transcript": row.get("transcript_text"),
            "business_id": row.get("business_id"),
        })
    return results


@router.get("/summaries")
async def list_summaries(business_id: UUID = None, limit: int = 50):
    """List summaries for active-tenant calls in frontend-friendly shape."""
    try:
        sb = get_backend_supabase()
        active_business_ids = get_active_business_ids(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if business_id:
        if str(business_id) not in active_business_ids:
            raise HTTPException(status_code=404, detail="Business not found")
        active_business_ids = [str(business_id)]
    if not active_business_ids:
        return []

    calls_resp = (
        sb.table("call_records")
        .select("id")
        .in_("business_id", active_business_ids)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    call_ids = [row["id"] for row in (calls_resp.data or [])]
    if not call_ids:
        return []

    resp = (
        sb.table("call_summaries")
        .select("*")
        .in_("call_record_id", call_ids)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    results = []
    for row in (resp.data or []):
        notes = row.get("structured_notes") or {}
        if not isinstance(notes, dict):
            notes = {}
        key_points = notes.get("key_points") or [
            value for value in [
                row.get("intent"),
                row.get("service_type"),
                row.get("urgency"),
                row.get("lead_quality"),
            ] if value
        ]
        action_items = notes.get("action_items") or []
        summary = notes.get("summary") or row.get("escalation_reason") or (
            f"{row.get('intent', 'unknown')} call, {row.get('lead_quality', 'unknown')} lead"
        )
        results.append({
            "id": row["id"],
            "call_id": row.get("call_record_id"),
            "summary": summary,
            "key_points": key_points,
            "action_items": action_items,
            "created_at": row.get("created_at", ""),
        })
    return results


@router.get("/calls", response_model=list[CallRecordResponse])
async def list_calls(business_id: UUID, limit: int = 50):
    """List call records for a business."""
    return list_call_records(business_id, limit)


@router.patch("/calls/{call_id}/transcript")
async def patch_transcript(call_id: UUID, transcript_text: str):
    """Update the transcript for a call record."""
    try:
        result = update_transcript(call_id, transcript_text)
        if not result:
            raise HTTPException(status_code=404, detail="Call record not found")
        return result
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# Call Summaries
# ---------------------------------------------------------------------------

@router.post("/summaries", status_code=status.HTTP_201_CREATED)
async def create_summary(data: CallSummaryCreate):
    """Create a call summary."""
    try:
        result = create_call_summary(data)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create summary")
        return result
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/calls/{call_id}/summary", response_model=CallSummaryResponse)
async def get_summary(call_id: UUID):
    """Get the summary for a call record."""
    result = get_call_summary(call_id)
    if not result:
        raise HTTPException(status_code=404, detail="Summary not found")
    return result


# ---------------------------------------------------------------------------
# Qualification
# ---------------------------------------------------------------------------

@router.post("/qualify", response_model=VoiceQualificationResult)
async def qualify_transcript(transcript_text: str):
    """Qualify a call from transcript text. Deterministic in v0.1."""
    return qualify_call_transcript(transcript_text)
