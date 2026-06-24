"""CRM-lite service — CRUD for leads, quotes, jobs, message drafts."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from chromagora_api.db.base import get_supabase
from chromagora_schemas.crm import (
    LeadCreate, LeadUpdate, LeadResponse,
    QuoteCreate, QuoteUpdate, QuoteResponse,
    JobCreate, JobUpdate, JobResponse,
    MessageDraftCreate, MessageDraftUpdate, MessageDraftResponse,
)


def _table(name: str):
    sb = get_supabase()
    if not sb:
        raise RuntimeError("Database not configured")
    return sb.table(name)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def create_lead(data: LeadCreate) -> dict[str, Any]:
    resp = _table("leads").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_lead(lead_id: UUID) -> Optional[dict[str, Any]]:
    resp = _table("leads").select("*").eq("id", str(lead_id)).execute()
    return resp.data[0] if resp.data else None


def list_leads(business_id: UUID, status: str | None = None) -> list[dict]:
    query = _table("leads").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_lead(lead_id: UUID, data: LeadUpdate) -> Optional[dict[str, Any]]:
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_lead(lead_id)
    update_data["updated_at"] = "now()"
    resp = _table("leads").update(update_data).eq("id", str(lead_id)).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

def create_quote(data: QuoteCreate) -> dict[str, Any]:
    resp = _table("quotes").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_quote(quote_id: UUID) -> Optional[dict[str, Any]]:
    resp = _table("quotes").select("*").eq("id", str(quote_id)).execute()
    return resp.data[0] if resp.data else None


def list_quotes(business_id: UUID, status: str | None = None) -> list[dict]:
    query = _table("quotes").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_quote(quote_id: UUID, data: QuoteUpdate) -> Optional[dict[str, Any]]:
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_quote(quote_id)
    update_data["updated_at"] = "now()"
    resp = _table("quotes").update(update_data).eq("id", str(quote_id)).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def create_job(data: JobCreate) -> dict[str, Any]:
    resp = _table("jobs").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_job(job_id: UUID) -> Optional[dict[str, Any]]:
    resp = _table("jobs").select("*").eq("id", str(job_id)).execute()
    return resp.data[0] if resp.data else None


def list_jobs(business_id: UUID, status: str | None = None) -> list[dict]:
    query = _table("jobs").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_job(job_id: UUID, data: JobUpdate) -> Optional[dict[str, Any]]:
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_job(job_id)
    update_data["updated_at"] = "now()"
    resp = _table("jobs").update(update_data).eq("id", str(job_id)).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Message Drafts
# ---------------------------------------------------------------------------

def create_message_draft(data: MessageDraftCreate) -> dict[str, Any]:
    resp = _table("message_drafts").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_message_draft(draft_id: UUID) -> Optional[dict[str, Any]]:
    resp = _table("message_drafts").select("*").eq("id", str(draft_id)).execute()
    return resp.data[0] if resp.data else None


def list_message_drafts(business_id: UUID, status: str | None = None) -> list[dict]:
    query = _table("message_drafts").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_message_draft(draft_id: UUID, data: MessageDraftUpdate) -> Optional[dict[str, Any]]:
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_message_draft(draft_id)
    update_data["updated_at"] = "now()"
    resp = _table("message_drafts").update(update_data).eq("id", str(draft_id)).execute()
    return resp.data[0] if resp.data else None
