"""CRM integration abstraction.

Allows swapping internal CRM-lite for external providers (HubSpot, GoHighLevel, Zoho).
InternalCrmLiteProvider uses Supabase tables (default).
External providers not implemented in v0.1 — interface only.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

CRM_PROVIDER = os.environ.get("CRM_PROVIDER", "internal")  # internal, hubspot, gohighlevel, zoho


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class CrmLead:
    """Normalized lead record."""
    def __init__(self, id: str, customer_name: str, customer_contact: str,
                 source: str | None = None, status: str = "new"):
        self.id = id
        self.customer_name = customer_name
        self.customer_contact = customer_contact
        self.source = source
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_contact": self.customer_contact,
            "source": self.source,
            "status": self.status,
        }


class CrmTask:
    """Normalized task record."""
    def __init__(self, id: str, title: str, related_lead_id: str | None = None,
                 status: str = "pending", due_date: str | None = None):
        self.id = id
        self.title = title
        self.related_lead_id = related_lead_id
        self.status = status
        self.due_date = due_date


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class CrmProvider(ABC):
    """Abstract CRM integration interface."""

    @abstractmethod
    def create_lead(self, business_id: UUID, lead: CrmLead) -> str:
        """Create a lead. Returns the lead ID."""
        ...

    @abstractmethod
    def update_lead(self, lead_id: str, updates: dict[str, Any]) -> bool:
        """Update a lead. Returns True if found and updated."""
        ...

    @abstractmethod
    def create_task(self, business_id: UUID, task: CrmTask) -> str:
        """Create a follow-up task. Returns the task ID."""
        ...

    @abstractmethod
    def get_lead(self, lead_id: str) -> Optional[CrmLead]:
        """Get a lead by ID. Returns None if not found."""
        ...

    @abstractmethod
    def list_recent_leads(self, business_id: UUID, limit: int = 20) -> list[CrmLead]:
        """List recent leads for a business."""
        ...


# ---------------------------------------------------------------------------
# Internal CRM-lite provider (Supabase-backed)
# ---------------------------------------------------------------------------

class InternalCrmLiteProvider(CrmProvider):
    """Internal CRM using Supabase tables (leads, quotes, jobs)."""

    def _get_supabase(self):
        from chromagora_api.db.base import get_supabase
        return get_supabase()

    def create_lead(self, business_id: UUID, lead: CrmLead) -> str:
        sb = self._get_supabase()
        if not sb:
            raise RuntimeError("Database not configured")

        data = {
            "business_id": str(business_id),
            "customer_name": lead.customer_name,
            "customer_contact": lead.customer_contact,
            "source": lead.source,
            "status": lead.status,
            "notes": "",
        }
        resp = sb.table("leads").insert(data).execute()
        if not resp.data:
            raise RuntimeError("Failed to create lead")
        lead.id = resp.data[0]["id"]
        return lead.id

    def update_lead(self, lead_id: str, updates: dict[str, Any]) -> bool:
        sb = self._get_supabase()
        if not sb:
            raise RuntimeError("Database not configured")

        updates["updated_at"] = "now()"
        resp = sb.table("leads").update(updates).eq("id", lead_id).execute()
        return bool(resp.data)

    def create_task(self, business_id: UUID, task: CrmTask) -> str:
        sb = self._get_supabase()
        if not sb:
            raise RuntimeError("Database not configured")

        data = {
            "business_id": str(business_id),
            "title": task.title,
            "status": task.status,
        }
        resp = sb.table("agent_tasks").insert(data).execute()
        if not resp.data:
            raise RuntimeError("Failed to create task")
        task.id = resp.data[0]["id"]
        return task.id

    def get_lead(self, lead_id: str) -> Optional[CrmLead]:
        sb = self._get_supabase()
        if not sb:
            return None

        resp = sb.table("leads").select("id, customer_name, customer_contact, source, status").eq("id", lead_id).execute()
        if not resp.data:
            return None
        row = resp.data[0]
        return CrmLead(
            id=row["id"],
            customer_name=row["customer_name"],
            customer_contact=row["customer_contact"],
            source=row.get("source"),
            status=row.get("status", "new"),
        )

    def list_recent_leads(self, business_id: UUID, limit: int = 20) -> list[CrmLead]:
        sb = self._get_supabase()
        if not sb:
            return []

        resp = (
            sb.table("leads")
            .select("id, customer_name, customer_contact, source, status")
            .eq("business_id", str(business_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [
            CrmLead(
                id=row["id"],
                customer_name=row["customer_name"],
                customer_contact=row["customer_contact"],
                source=row.get("source"),
                status=row.get("status", "new"),
            )
            for row in (resp.data or [])
        ]


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

def get_crm_provider() -> CrmProvider:
    """Get the configured CRM provider."""
    if CRM_PROVIDER == "internal":
        return InternalCrmLiteProvider()
    elif CRM_PROVIDER == "hubspot":
        raise NotImplementedError("HubSpot provider not implemented in v0.1")
    elif CRM_PROVIDER == "gohighlevel":
        raise NotImplementedError("GoHighLevel provider not implemented in v0.1")
    elif CRM_PROVIDER == "zoho":
        raise NotImplementedError("Zoho provider not implemented in v0.1")
    else:
        logger.warning("Unknown CRM_PROVIDER=%s, falling back to internal", CRM_PROVIDER)
        return InternalCrmLiteProvider()
