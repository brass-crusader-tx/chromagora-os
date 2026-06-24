"""Mobile readiness service — /mobile endpoints backed by Supabase."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_api.db.base import get_supabase


def _table(name: str):
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")
    return sb.table(name)


# ---------------------------------------------------------------------------
# GET /mobile/today
# ---------------------------------------------------------------------------

def get_mobile_today(business_id: UUID) -> dict[str, Any]:
    """Return a mobile dashboard snapshot for a business.

    Aggregates: urgent approvals, high-priority events, active workflow
    waits, upcoming jobs, opportunity deadlines, blocked agents.
    """
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    bid = str(business_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_ahead = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # 1. Urgent pending approvals
    approvals_resp = (
        sb.table("approval_requests")
        .select("id, action_proposal_id, status, requested_at, expires_at")
        .eq("business_id", bid)
        .eq("status", "pending")
        .order("requested_at", desc=True)
        .limit(10)
        .execute()
    )
    urgent_approvals = approvals_resp.data or []

    # 2. High-priority recent events (last 24h)
    events_resp = (
        sb.table("events")
        .select("id, event_type, source_type, payload_json, occurred_at")
        .eq("business_id", bid)
        .gte("occurred_at", today_start)
        .order("occurred_at", desc=True)
        .limit(20)
        .execute()
    )
    recent_events = events_resp.data or []

    # 3. Active workflow runs waiting for approval or external event
    workflows_resp = (
        sb.table("workflow_runs")
        .select("id, workflow_type, status, current_step, started_at, updated_at")
        .eq("business_id", bid)
        .in_("status", ["waiting_for_approval", "waiting_for_external_event", "running"])
        .order("updated_at", desc=True)
        .limit(10)
        .execute()
    )
    active_workflows = workflows_resp.data or []

    # 4. Upcoming jobs (scheduled within next 7 days)
    jobs_resp = (
        sb.table("jobs")
        .select("id, customer_name, service_type, status, scheduled_at, completed_at")
        .eq("business_id", bid)
        .in_("status", ["scheduled", "in_progress"])
        .gte("scheduled_at", now_iso)
        .lte("scheduled_at", week_ahead)
        .order("scheduled_at")
        .limit(10)
        .execute()
    )
    upcoming_jobs = jobs_resp.data or []

    # 5. Active opportunities with approaching deadlines
    opportunities_resp = (
        sb.table("opportunities")
        .select("id, title, status, deadline_at, estimated_value_max, fit_score")
        .eq("business_id", bid)
        .in_("status", ["qualifying", "qualified", "pursuing"])
        .gte("deadline_at", now_iso)
        .order("deadline_at")
        .limit(10)
        .execute()
    )
    upcoming_opportunities = opportunities_resp.data or []

    # 6. Blocked / failed agent runs
    agents_resp = (
        sb.table("agent_runs")
        .select("id, agent_type, status, error_message, started_at, completed_at")
        .eq("business_id", bid)
        .in_("status", ["failed", "cancelled"])
        .gte("started_at", today_start)
        .order("started_at", desc=True)
        .limit(5)
        .execute()
    )
    blocked_agents = agents_resp.data or []

    return {
        "business_id": str(business_id),
        "generated_at": now_iso,
        "urgent_approvals": urgent_approvals,
        "recent_events": recent_events,
        "active_workflows": active_workflows,
        "upcoming_jobs": upcoming_jobs,
        "upcoming_opportunities": upcoming_opportunities,
        "blocked_agents": blocked_agents,
    }


# ---------------------------------------------------------------------------
# GET /mobile/approvals
# ---------------------------------------------------------------------------

def list_mobile_approvals(business_id: UUID, status: str = "pending") -> list[dict]:
    """List approval requests for mobile, with action proposal context."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    bid = str(business_id)

    resp = (
        sb.table("approval_requests")
        .select(
            "id, action_proposal_id, status, requested_at, decided_at, "
            "decision_notes, expires_at, requested_by_type"
        )
        .eq("business_id", bid)
        .eq("status", status)
        .order("requested_at", desc=True)
        .limit(20)
        .execute()
    )
    approvals = resp.data or []

    # Enrich with action proposal title/description
    proposal_ids = [a["action_proposal_id"] for a in approvals if a.get("action_proposal_id")]
    proposals_map: dict[str, dict] = {}
    if proposal_ids:
        # Batch fetch — Supabase py doesn't support .in() with UUID list directly in all versions
        for pid in proposal_ids:
            p_resp = (
                sb.table("action_proposals")
                .select("id, title, description, action_type, risk_level")
                .eq("id", pid)
                .execute()
            )
            if p_resp.data:
                proposals_map[str(p_resp.data[0]["id"])] = p_resp.data[0]

    for a in approvals:
        pid = a.get("action_proposal_id")
        a["action_proposal"] = proposals_map.get(pid) if pid else None

    return approvals


# ---------------------------------------------------------------------------
# POST /mobile/approvals/{id}/approve and /reject
# ---------------------------------------------------------------------------

def mobile_approve(approval_id: UUID, decided_by: str = "operator") -> Optional[dict]:
    """Approve an approval request from mobile."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": "approved",
        "decided_by": decided_by,
        "decided_at": now,
        "updated_at": now,
    }
    resp = (
        sb.table("approval_requests")
        .update(update_data)
        .eq("id", str(approval_id))
        .execute()
    )
    return resp.data[0] if resp.data else None


def mobile_reject(approval_id: UUID, decided_by: str = "operator", notes: str | None = None) -> Optional[dict]:
    """Reject an approval request from mobile."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": "rejected",
        "decided_by": decided_by,
        "decided_at": now,
        "decision_notes": notes,
        "updated_at": now,
    }
    resp = (
        sb.table("approval_requests")
        .update(update_data)
        .eq("id", str(approval_id))
        .execute()
    )
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# GET /mobile/command-feed
# ---------------------------------------------------------------------------

def get_mobile_command_feed(business_id: UUID, limit: int = 30) -> list[dict]:
    """Return recent events for the mobile command feed."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    resp = (
        sb.table("events")
        .select("id, event_type, source_type, source_id, payload_json, occurred_at, trace_id")
        .eq("business_id", str(business_id))
        .order("occurred_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------------------------
# GET /mobile/jobs/today
# ---------------------------------------------------------------------------

def get_mobile_jobs_today(business_id: UUID) -> list[dict]:
    """Return today's jobs for mobile field view."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    resp = (
        sb.table("jobs")
        .select("id, customer_name, service_type, status, scheduled_at, completed_at, notes")
        .eq("business_id", str(business_id))
        .gte("scheduled_at", today_start)
        .lt("scheduled_at", today_end)
        .order("scheduled_at")
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------------------------
# POST /mobile/capture/note
# ---------------------------------------------------------------------------

def capture_note(
    business_id: UUID,
    content: str,
    job_id: UUID | None = None,
    lead_id: UUID | None = None,
    note_type: str = "field_note",
) -> dict[str, Any]:
    """Capture a field note. Stores as an event record."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "business_id": str(business_id),
        "event_type": "mobile.note_captured",
        "source_type": "mobile_capture",
        "source_id": None,
        "payload_json": {
            "content": content,
            "note_type": note_type,
            "job_id": str(job_id) if job_id else None,
            "lead_id": str(lead_id) if lead_id else None,
        },
        "occurred_at": now,
        "created_at": now,
    }
    resp = sb.table("events").insert(payload).execute()
    return resp.data[0] if resp.data else {}


# ---------------------------------------------------------------------------
# POST /mobile/capture/photo-metadata
# ---------------------------------------------------------------------------

def capture_photo_metadata(
    business_id: UUID,
    photo_url: str | None = None,
    job_id: UUID | None = None,
    lead_id: UUID | None = None,
    caption: str | None = None,
    taken_at: datetime | None = None,
) -> dict[str, Any]:
    """Capture photo metadata from mobile. No actual file upload — just a reference."""
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "business_id": str(business_id),
        "event_type": "mobile.photo_captured",
        "source_type": "mobile_capture",
        "source_id": None,
        "payload_json": {
            "photo_url": photo_url,
            "caption": caption,
            "job_id": str(job_id) if job_id else None,
            "lead_id": str(lead_id) if lead_id else None,
            "taken_at": taken_at.isoformat() if taken_at else now,
        },
        "occurred_at": now,
        "created_at": now,
    }
    resp = sb.table("events").insert(payload).execute()
    return resp.data[0] if resp.data else {}
