"""Quote follow-up runtime routes — detection, event processing, traces."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_backend_supabase, get_business_tenant_id
from chromagora_api.services.quote_stale_detector import detect_stale_quotes
from chromagora_api.services.event_dispatcher import process_pending_events, process_single_event

router = APIRouter(tags=["quote-follow-up"])


@router.post("/businesses/{business_id}/quotes/detect-stale")
async def detect_stale(business_id: UUID):
    """Detect stale quotes for a business and emit quote.stale events.

    Idempotent — running twice won't create duplicate events.
    """
    try:
        sb = get_backend_supabase()
        tenant_id = get_business_tenant_id(str(business_id), sb)
        if not tenant_id:
            raise HTTPException(status_code=404, detail="Business not found")
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    results = detect_stale_quotes(
        business_id=business_id,
        tenant_id=UUID(tenant_id),
    )
    return {"detected": len(results), "results": results}


@router.post("/events/process")
async def process_events(
    event_type: str | None = None,
    limit: int = 50,
):
    """Process pending events (dispatches to handlers)."""
    try:
        get_backend_supabase()
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    results = process_pending_events(event_type=event_type, limit=limit)
    return {"processed": len(results), "results": results}


@router.post("/events/{event_id}/process")
async def process_event(event_id: UUID):
    """Process a single event by ID."""
    result = process_single_event(event_id)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get all records connected by a trace_id."""
    try:
        sb = get_backend_supabase()
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    trace = {
        "trace_id": trace_id,
        "events": [],
        "agent_runs": [],
        "action_proposals": [],
        "approval_requests": [],
        "action_executions": [],
        "crm_tasks": [],
        "message_drafts": [],
        "structured_logs": [],
    }

    for table, key in [
        ("events", "events"),
        ("agent_runs", "agent_runs"),
        ("action_proposals", "action_proposals"),
        ("approval_requests", "approval_requests"),
        ("action_executions", "action_executions"),
        ("crm_tasks", "crm_tasks"),
        ("message_drafts", "message_drafts"),
        ("structured_logs", "structured_logs"),
    ]:
        try:
            resp = (
                sb.table(table)
                .select("*")
                .eq("trace_id", trace_id)
                .execute()
            )
            trace[key] = resp.data or []
        except Exception:
            pass  # Table or column may not exist yet

    return trace


@router.get("/businesses/{business_id}/crm-tasks")
async def list_crm_tasks(business_id: UUID, status: str | None = None):
    """List CRM tasks for a business."""
    try:
        sb = get_backend_supabase()
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    query = (
        sb.table("crm_tasks")
        .select("*")
        .eq("business_id", str(business_id))
        .order("created_at", desc=True)
    )
    if status:
        query = query.eq("status", status)

    try:
        resp = query.execute()
        return resp.data or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load CRM tasks: {exc}")
