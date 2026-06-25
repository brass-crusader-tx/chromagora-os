"""CRM-lite service — CRUD for leads, quotes, jobs, message drafts."""

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID

from chromagora_api.db.tenant import get_backend_supabase, get_business_tenant_id
from chromagora_schemas.crm import (
    LeadCreate, LeadUpdate, LeadResponse,
    QuoteCreate, QuoteUpdate, QuoteResponse,
    JobCreate, JobUpdate, JobResponse,
    MessageDraftCreate, MessageDraftUpdate, MessageDraftResponse,
)


def _table(name: str):
    return get_backend_supabase().table(name)


def _get_supabase():
    return get_backend_supabase()


def _ensure_business_scope(sb, business_id: UUID) -> None:
    if not get_business_tenant_id(str(business_id), sb):
        raise RuntimeError("Business not found")


def _get_scoped_record(sb, table: str, record_id: UUID) -> Optional[dict[str, Any]]:
    resp = sb.table(table).select("*").eq("id", str(record_id)).execute()
    if not resp.data:
        return None
    row = resp.data[0]
    if row.get("business_id"):
        _ensure_business_scope(sb, UUID(row["business_id"]))
    return row


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def create_lead(data: LeadCreate) -> dict[str, Any]:
    sb = _get_supabase()
    _ensure_business_scope(sb, data.business_id)
    payload = data.model_dump(mode="json")
    try:
        resp = sb.table("leads").insert(payload).execute()
    except Exception as exc:
        if not _looks_like_missing_contact_columns(exc):
            raise
        fallback = _lead_payload_without_contact_columns(payload)
        resp = sb.table("leads").insert(fallback).execute()
    return resp.data[0] if resp.data else {}


def _looks_like_missing_contact_columns(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "contact_email" in message
        or "contact_phone" in message
        or "company_name" in message
        or "contact_title" in message
        or "could not find" in message and "schema cache" in message
    )


def _lead_payload_without_contact_columns(payload: dict[str, Any]) -> dict[str, Any]:
    contact_meta = {
        "email": payload.pop("contact_email", None),
        "phone": payload.pop("contact_phone", None),
        "company": payload.pop("company_name", None),
        "title": payload.pop("contact_title", None),
    }
    contact_meta = {k: v for k, v in contact_meta.items() if v}
    if contact_meta:
        marker = f"[contact_metadata]{json.dumps(contact_meta, sort_keys=True)}"
        payload["notes"] = f"{payload.get('notes') or ''}\n\n{marker}".strip()
    return payload


def get_lead(lead_id: UUID) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    return _get_scoped_record(sb, "leads", lead_id)


def list_leads(business_id: UUID, status: str | None = None) -> list[dict]:
    sb = _get_supabase()
    _ensure_business_scope(sb, business_id)
    query = sb.table("leads").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_lead(lead_id: UUID, data: LeadUpdate) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    if not _get_scoped_record(sb, "leads", lead_id):
        return None
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_lead(lead_id)
    update_data["updated_at"] = "now()"
    resp = sb.table("leads").update(update_data).eq("id", str(lead_id)).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

def create_quote(data: QuoteCreate) -> dict[str, Any]:
    sb = _get_supabase()
    _ensure_business_scope(sb, data.business_id)
    resp = sb.table("quotes").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_quote(quote_id: UUID) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    return _get_scoped_record(sb, "quotes", quote_id)


def list_quotes(business_id: UUID, status: str | None = None) -> list[dict]:
    sb = _get_supabase()
    _ensure_business_scope(sb, business_id)
    query = sb.table("quotes").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_quote(quote_id: UUID, data: QuoteUpdate) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    if not _get_scoped_record(sb, "quotes", quote_id):
        return None
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_quote(quote_id)
    update_data["updated_at"] = "now()"
    resp = sb.table("quotes").update(update_data).eq("id", str(quote_id)).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def create_job(data: JobCreate) -> dict[str, Any]:
    sb = _get_supabase()
    _ensure_business_scope(sb, data.business_id)
    resp = sb.table("jobs").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_job(job_id: UUID) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    return _get_scoped_record(sb, "jobs", job_id)


def list_jobs(business_id: UUID, status: str | None = None) -> list[dict]:
    sb = _get_supabase()
    _ensure_business_scope(sb, business_id)
    query = sb.table("jobs").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_job(job_id: UUID, data: JobUpdate) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    if not _get_scoped_record(sb, "jobs", job_id):
        return None
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_job(job_id)
    update_data["updated_at"] = "now()"
    resp = sb.table("jobs").update(update_data).eq("id", str(job_id)).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Message Drafts
# ---------------------------------------------------------------------------

def create_message_draft(data: MessageDraftCreate) -> dict[str, Any]:
    sb = _get_supabase()
    _ensure_business_scope(sb, data.business_id)
    resp = sb.table("message_drafts").insert(data.model_dump(mode="json")).execute()
    return resp.data[0] if resp.data else {}


def get_message_draft(draft_id: UUID) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    return _get_scoped_record(sb, "message_drafts", draft_id)


def list_message_drafts(business_id: UUID, status: str | None = None) -> list[dict]:
    sb = _get_supabase()
    _ensure_business_scope(sb, business_id)
    query = sb.table("message_drafts").select("*").eq("business_id", str(business_id))
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


def update_message_draft(draft_id: UUID, data: MessageDraftUpdate) -> Optional[dict[str, Any]]:
    sb = _get_supabase()
    if not _get_scoped_record(sb, "message_drafts", draft_id):
        return None
    update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    if not update_data:
        return get_message_draft(draft_id)
    update_data["updated_at"] = "now()"
    resp = sb.table("message_drafts").update(update_data).eq("id", str(draft_id)).execute()
    return resp.data[0] if resp.data else None
