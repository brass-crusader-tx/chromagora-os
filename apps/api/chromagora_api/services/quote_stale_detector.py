"""Quote stale detector — finds quotes that have gone inactive.

Deterministic detector that:
1. Finds quotes matching staleness criteria
2. Emits quote.stale events (idempotent)
3. Marks quotes as stale/follow_up_pending
4. Returns results for caller to dispatch agent processing
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_api.services.trace_propagation import ensure_trace_id, log_structured_event

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


# ---------------------------------------------------------------------------
# Business follow-up settings helpers
# ---------------------------------------------------------------------------

def _get_business_follow_up_settings(business_id: UUID, sb) -> dict[str, Any]:
    """Load follow-up settings from business_preferences.

    Returns defaults if no preferences are set.
    """
    defaults = {
        "stale_quote_threshold_days": 3,
        "follow_up_interval_days": 3,
        "max_quote_follow_ups": 3,
        "quote_follow_up_requires_approval": True,
        "preferred_follow_up_channel": "email",
        "follow_up_tone": None,
    }
    try:
        resp = (
            sb.table("business_preferences")
            .select("key, value_json")
            .eq("business_id", str(business_id))
            .in_("key", list(defaults.keys()))
            .execute()
        )
        for row in resp.data or []:
            key = row["key"]
            value = row.get("value_json", {})
            if isinstance(value, dict) and "value" in value:
                defaults[key] = value["value"]
            elif isinstance(value, (int, float, bool, str)):
                defaults[key] = value
    except Exception as exc:
        logger.warning("Failed to load business follow-up settings: %s", exc)
    return defaults


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

def detect_stale_quotes(
    business_id: UUID,
    tenant_id: Optional[UUID] = None,
) -> list[dict[str, Any]]:
    """Detect stale quotes for a business and emit quote.stale events.

    Returns list of detection results including quote_id, trace_id, event_id.
    Idempotent: will not emit duplicate events for the same quote/follow_up cycle.
    """
    sb = _get_supabase()
    if not sb:
        return []

    # Resolve tenant_id if not provided
    if not tenant_id:
        from chromagora_api.db.tenant import get_business_tenant_id
        tid = get_business_tenant_id(str(business_id), sb)
        if not tid:
            return []
        tenant_id = UUID(tid)

    # Load business follow-up settings
    settings = _get_business_follow_up_settings(business_id, sb)
    threshold_days = settings["stale_quote_threshold_days"]
    follow_up_interval_days = settings["follow_up_interval_days"]
    max_follow_ups = settings["max_quote_follow_ups"]

    now = datetime.now(timezone.utc)
    threshold_at = now - timedelta(days=threshold_days)

    # Find quotes eligible for staleness detection
    # status in ('sent', 'followed_up') — followed_up quotes may need another follow-up
    # sent_at must not be null and must be older than threshold
    # follow_up_count must be less than max
    try:
        resp = (
            sb.table("quotes")
            .select("*")
            .eq("business_id", str(business_id))
            .in_("status", ["sent", "followed_up"])
            .not_.is_("sent_at", "null")
            .lt("sent_at", threshold_at.isoformat())
            .execute()
        )
        candidates = resp.data or []
    except Exception as exc:
        logger.error("Failed to query quotes for staleness: %s", exc)
        return []

    results = []
    for quote in candidates:
        follow_up_count = quote.get("follow_up_count") or 0
        if follow_up_count >= max_follow_ups:
            continue

        # Check if there's already an unresolved proposal/approval for this quote+cycle
        idempotency_key = f"quote.stale:{quote['id']}:{follow_up_count}"
        existing_event = _check_existing_stale_event(sb, tenant_id, idempotency_key)
        if existing_event:
            continue

        # Check if there's a pending approval for this quote
        existing_proposal = _check_unresolved_proposal(sb, tenant_id, quote["id"])
        if existing_proposal:
            continue

        # Check the repeat follow-up schedule before emitting a new event.
        next_follow_up_at = _parse_timestamp(quote.get("next_follow_up_at"))
        if next_follow_up_at and next_follow_up_at > now:
            continue

        last_followup = quote.get("last_followup_at")
        if last_followup:
            last_dt = _parse_timestamp(last_followup)
            interval_at = now - timedelta(days=follow_up_interval_days)
            if last_dt and last_dt > interval_at:
                # Last follow-up was inside the configured follow-up interval.
                continue

        # Emit quote.stale event
        trace_id = ensure_trace_id()
        result = _emit_stale_event(
            sb=sb,
            tenant_id=tenant_id,
            business_id=business_id,
            quote=quote,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            settings=settings,
        )
        if result:
            results.append(result)

    # Structured log
    if results:
        log_structured_event(
            tenant_id=tenant_id,
            trace_id="detector",
            service_name="quote_stale_detector",
            event_type="detection_run",
            message=f"Detected {len(results)} stale quotes for business {business_id}",
            context={"business_id": str(business_id), "count": len(results)},
        )

    return results


def _check_existing_stale_event(sb, tenant_id: UUID, idempotency_key: str) -> bool:
    """Check if a quote.stale event with this idempotency key already exists."""
    try:
        resp = (
            sb.table("events")
            .select("id")
            .eq("tenant_id", str(tenant_id))
            .eq("idempotency_key", idempotency_key)
            .execute()
        )
        return bool(resp.data)
    except Exception:
        # If idempotency_key column doesn't exist yet, skip check
        return False


def _check_unresolved_proposal(sb, tenant_id: UUID, quote_id: str) -> bool:
    """Check if there's an unresolved action_proposal for this quote."""
    try:
        resp = (
            sb.table("action_proposals")
            .select("id")
            .eq("tenant_id", str(tenant_id))
            .eq("quote_id", quote_id)
            .in_("status", ["proposed", "approval_required", "draft"])
            .execute()
        )
        return bool(resp.data)
    except Exception:
        # If quote_id column doesn't exist yet, skip check
        return False


def _emit_stale_event(
    sb,
    tenant_id: UUID,
    business_id: UUID,
    quote: dict,
    idempotency_key: str,
    trace_id: str,
    settings: dict,
) -> Optional[dict[str, Any]]:
    """Emit a quote.stale event and update the quote status.

    Returns detection result dict or None on failure.
    """
    quote_id = quote["id"]
    follow_up_count = quote.get("follow_up_count") or 0
    contact = _load_quote_contact(sb, quote)

    # Build event payload
    sent_at = quote.get("sent_at", "")
    try:
        sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
        days_since_sent = (datetime.now(timezone.utc) - sent_dt).days
    except (ValueError, AttributeError):
        days_since_sent = 0

    payload = {
        "quote_id": quote_id,
        "business_id": str(business_id),
        "lead_id": quote.get("lead_id"),
        "customer_id": quote.get("customer_id"),
        "customer_name": contact.get("customer_name"),
        "customer_contact": contact.get("customer_contact"),
        "contact_email": contact.get("contact_email"),
        "contact_phone": contact.get("contact_phone"),
        "company_name": contact.get("company_name"),
        "service_type": quote.get("service_type"),
        "quote_amount": quote.get("quote_amount"),
        "currency": quote.get("currency", "CAD"),
        "description": quote.get("description"),
        "status": quote.get("status"),
        "sent_at": sent_at,
        "days_since_sent": days_since_sent,
        "follow_up_count": follow_up_count,
        "max_follow_ups": settings["max_quote_follow_ups"],
        "stale_threshold_days": settings["stale_quote_threshold_days"],
        "follow_up_interval_days": settings["follow_up_interval_days"],
        "requires_approval": settings["quote_follow_up_requires_approval"],
        "preferred_channel": settings["preferred_follow_up_channel"],
    }

    # Insert event
    event_id = str(uuid4())
    try:
        sb.table("events").insert({
            "id": event_id,
            "tenant_id": str(tenant_id),
            "business_id": str(business_id),
            "event_type": "quote.stale",
            "source_type": "detector",
            "source_id": quote_id,
            "entity_type": "quote",
            "entity_id": quote_id,
            "payload_json": payload,
            "idempotency_key": idempotency_key,
            "trace_id": trace_id,
        }).execute()
    except Exception as exc:
        logger.error("Failed to emit quote.stale event: %s", exc)
        return None

    # Update quote status to stale if current status is 'sent'
    current_status = quote.get("status", "sent")
    new_status = "stale" if current_status == "sent" else current_status
    try:
        update_data: dict[str, Any] = {
            "stale_detected_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if new_status != current_status:
            update_data["status"] = new_status
        sb.table("quotes").update(update_data).eq("id", quote_id).execute()
    except Exception as exc:
        logger.warning("Failed to update quote stale_detected_at: %s", exc)

    return {
        "quote_id": quote_id,
        "event_id": event_id,
        "trace_id": trace_id,
        "idempotency_key": idempotency_key,
        "days_since_sent": days_since_sent,
        "follow_up_count": follow_up_count,
        "new_status": new_status,
    }


def _load_quote_contact(sb, quote: dict[str, Any]) -> dict[str, Any]:
    """Load customer contact fields for the quote payload when a lead is linked."""
    contact = {
        "customer_name": quote.get("customer_name"),
        "customer_contact": quote.get("customer_contact"),
        "contact_email": quote.get("contact_email"),
        "contact_phone": quote.get("contact_phone"),
        "company_name": quote.get("company_name"),
    }
    lead_id = quote.get("lead_id")
    if not lead_id:
        return contact

    try:
        resp = (
            sb.table("leads")
            .select("customer_name, customer_contact, contact_email, contact_phone, company_name")
            .eq("id", lead_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.warning("Failed to load quote lead contact for %s: %s", lead_id, exc)
        return contact

    if not resp.data:
        return contact

    lead = resp.data[0]
    contact["customer_name"] = contact["customer_name"] or lead.get("customer_name")
    contact["customer_contact"] = contact["customer_contact"] or lead.get("customer_contact")
    contact["contact_email"] = contact["contact_email"] or lead.get("contact_email")
    contact["contact_phone"] = contact["contact_phone"] or lead.get("contact_phone")
    contact["company_name"] = contact["company_name"] or lead.get("company_name")
    return contact


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse a timestamp value from Supabase/PostgREST into an aware datetime."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
