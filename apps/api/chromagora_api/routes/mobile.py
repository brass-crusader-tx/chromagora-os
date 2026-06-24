"""Mobile readiness endpoints — /mobile API surface.

Provides a mobile-optimized view of the system for field use.
Thin, API-driven. Not the native Android app (that's Chapter 24).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.services.mobile_service import (
    get_mobile_today,
    list_mobile_approvals,
    mobile_approve,
    mobile_reject,
    get_mobile_command_feed,
    get_mobile_jobs_today,
    capture_note,
    capture_photo_metadata,
)
from chromagora_schemas.crm import (
    MobileNoteCapture,
    MobilePhotoMetadata,
)

router = APIRouter(prefix="/mobile", tags=["mobile"])


# ---------------------------------------------------------------------------
# GET /mobile/today — dashboard snapshot
# ---------------------------------------------------------------------------

@router.get("/today")
async def mobile_today(business_id: UUID):
    """Mobile dashboard: urgent approvals, events, workflows, jobs, opportunities."""
    try:
        return get_mobile_today(business_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# GET /mobile/approvals — list pending approvals
# ---------------------------------------------------------------------------

@router.get("/approvals")
async def mobile_approvals_list(business_id: UUID, status: str = "pending"):
    """List approval requests for mobile."""
    try:
        return list_mobile_approvals(business_id, status)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# POST /mobile/approvals/{id}/approve
# ---------------------------------------------------------------------------

@router.post("/approvals/{approval_id}/approve")
async def mobile_approve_endpoint(approval_id: UUID):
    """Approve an approval request from mobile."""
    result = mobile_approve(approval_id)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found")
    return result


# ---------------------------------------------------------------------------
# POST /mobile/approvals/{id}/reject
# ---------------------------------------------------------------------------

@router.post("/approvals/{approval_id}/reject")
async def mobile_reject_endpoint(approval_id: UUID, notes: Optional[str] = None):
    """Reject an approval request from mobile."""
    result = mobile_reject(approval_id, notes=notes)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found")
    return result


# ---------------------------------------------------------------------------
# GET /mobile/command-feed — recent events
# ---------------------------------------------------------------------------

@router.get("/command-feed")
async def mobile_command_feed(business_id: UUID, limit: int = 30):
    """Recent events for the mobile command feed."""
    try:
        return get_mobile_command_feed(business_id, limit)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# GET /mobile/jobs/today — today's jobs
# ---------------------------------------------------------------------------

@router.get("/jobs/today")
async def mobile_jobs_today(business_id: UUID):
    """Today's scheduled jobs for mobile field view."""
    try:
        return get_mobile_jobs_today(business_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# POST /mobile/capture/note — field note capture
# ---------------------------------------------------------------------------

@router.post("/capture/note", status_code=status.HTTP_201_CREATED)
async def mobile_capture_note(data: MobileNoteCapture):
    """Capture a field note from mobile."""
    try:
        return capture_note(
            business_id=data.business_id,
            content=data.content,
            job_id=data.job_id,
            lead_id=data.lead_id,
            note_type=data.note_type,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# POST /mobile/capture/photo-metadata — photo metadata capture
# ---------------------------------------------------------------------------

@router.post("/capture/photo-metadata", status_code=status.HTTP_201_CREATED)
async def mobile_capture_photo(data: MobilePhotoMetadata):
    """Capture photo metadata from mobile. No actual file upload."""
    try:
        return capture_photo_metadata(
            business_id=data.business_id,
            photo_url=data.photo_url,
            job_id=data.job_id,
            lead_id=data.lead_id,
            caption=data.caption,
            taken_at=data.taken_at,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
