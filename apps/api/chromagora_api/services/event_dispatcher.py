"""Event dispatcher — routes events to the correct handler.

The dispatcher is intentionally still small, but it now has the minimum
runtime mechanics needed for a real polling worker: event claiming, retry
tracking, backoff, dead-letter status, and handler-result-aware completion.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_api.services.runtime_utils import run_awaitable_blocking
from chromagora_api.services.trace_propagation import ensure_trace_id, log_structured_event

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


# ---------------------------------------------------------------------------
# Event type → handler mapping
# ---------------------------------------------------------------------------

_EVENT_HANDLERS: dict[str, str] = {
    "quote.stale": "chromagora_api.services.quote_stale_handler.handle_quote_stale_event",
}

_TERMINAL_FAILURE_STATUSES = {"error", "failed"}
_RETRYABLE_EVENT_STATUSES = {None, "pending", "failed"}


def process_pending_events(
    tenant_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    worker_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Process pending events.

    Events are claimed before dispatch. A handler must return a successful
    result before ``processed_at`` is set. Retryable failures are left
    unprocessed and moved to ``failed`` or ``dead_letter``.
    """
    sb = _get_supabase()
    if not sb:
        return []

    worker_id = worker_id or f"dispatcher:{os.getpid()}"
    events = _load_pending_events(sb, tenant_id=tenant_id, event_type=event_type, limit=limit)

    results: list[dict[str, Any]] = []
    for event in events:
        claimed = _claim_event(event, worker_id=worker_id)
        if not claimed:
            continue
        result = _dispatch_event(claimed, worker_id=worker_id)
        results.append(result)

    return results


def process_single_event(event_id: UUID, worker_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Process a single event by ID."""
    sb = _get_supabase()
    if not sb:
        return None

    try:
        resp = sb.table("events").select("*").eq("id", str(event_id)).execute()
        if not resp.data:
            return None
        event = resp.data[0]
    except Exception as exc:
        logger.error("Failed to fetch event %s: %s", event_id, exc)
        return None

    claimed = _claim_event(event, worker_id=worker_id or f"dispatcher:{os.getpid()}")
    if not claimed:
        return {
            "event_id": str(event_id),
            "status": "not_claimed",
            "trace_id": event.get("trace_id") or ensure_trace_id(),
        }
    return _dispatch_event(claimed, worker_id=worker_id)


def _load_pending_events(sb, tenant_id: Optional[UUID], event_type: Optional[str], limit: int) -> list[dict[str, Any]]:
    query = (
        sb.table("events")
        .select("*")
        .is_("processed_at", "null")
        .order("occurred_at", desc=False)
        .limit(limit)
    )

    if tenant_id:
        query = query.eq("tenant_id", str(tenant_id))
    if event_type:
        query = query.eq("event_type", event_type)

    try:
        resp = query.execute()
        events = resp.data or []
    except Exception as exc:
        logger.warning("Failed to query unprocessed events: %s", exc)
        return []

    now = datetime.now(timezone.utc)
    ready: list[dict[str, Any]] = []
    for event in events:
        status = event.get("status")
        if status not in _RETRYABLE_EVENT_STATUSES:
            continue
        next_attempt_at = event.get("next_attempt_at")
        if next_attempt_at:
            try:
                next_dt = datetime.fromisoformat(str(next_attempt_at).replace("Z", "+00:00"))
                if next_dt > now:
                    continue
            except ValueError:
                pass
        ready.append(event)
    return ready


def _claim_event(event: dict[str, Any], worker_id: str) -> Optional[dict[str, Any]]:
    """Claim an event for this worker.

    This is best-effort with Supabase/PostgREST. The migration adds status and
    claim columns; older DBs fall back to returning the event without a claim.
    """
    event_id = event.get("id")
    if not event_id:
        return None

    retry_count = int(event.get("retry_count") or 0)
    max_retries = int(event.get("max_retries") or 5)
    if retry_count >= max_retries:
        _mark_dead_letter(event, "Retry budget already exhausted before claim")
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    update = {
        "status": "processing",
        "claimed_by": worker_id,
        "claimed_at": now_iso,
        "retry_count": retry_count + 1,
    }

    sb = _get_supabase()
    if not sb:
        return None

    try:
        query = sb.table("events").update(update).eq("id", event_id).is_("processed_at", "null")
        if event.get("status"):
            query = query.eq("status", event.get("status"))
        resp = query.execute()
        if resp.data:
            return resp.data[0]
        # Some mocks/clients do not return updated rows. Preserve forward progress.
        return {**event, **update}
    except Exception as exc:
        logger.warning("Event claim failed for %s; falling back to unclaimed dispatch: %s", event_id, exc)
        return event


def _dispatch_event(event: dict[str, Any], worker_id: Optional[str] = None) -> dict[str, Any]:
    """Dispatch an event to its handler and mark it based on actual outcome."""
    event_type = event.get("event_type", "")
    event_id = event.get("id", "")
    trace_id = event.get("trace_id") or ensure_trace_id()

    handler_path = _EVENT_HANDLERS.get(event_type)
    if not handler_path:
        _mark_processed(event_id)
        return {
            "event_id": event_id,
            "event_type": event_type,
            "status": "no_handler",
            "trace_id": trace_id,
        }

    try:
        module_path, func_name = handler_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)

        if asyncio.iscoroutinefunction(handler):
            result = run_awaitable_blocking(handler(event))
        else:
            result = handler(event)

        if not _handler_succeeded(result):
            error = _handler_error_message(result)
            _mark_failed(event, error)
            return {
                "event_id": event_id,
                "event_type": event_type,
                "status": "failed",
                "trace_id": trace_id,
                "handler_result": result,
                "error": error,
            }

        _mark_processed(event_id)

        log_structured_event(
            tenant_id=UUID(event["tenant_id"]) if event.get("tenant_id") else UUID(int=0),
            trace_id=trace_id,
            service_name="event_dispatcher",
            event_type="event_processed",
            message=f"Event {event_type} processed successfully",
            context={"event_id": event_id, "handler": handler_path, "worker_id": worker_id},
        )

        return {
            "event_id": event_id,
            "event_type": event_type,
            "status": "processed",
            "trace_id": trace_id,
            "handler_result": result,
        }

    except Exception as exc:
        logger.exception("Handler failed for event %s (%s): %s", event_id, event_type, exc)
        _mark_failed(event, str(exc))

        log_structured_event(
            tenant_id=UUID(event["tenant_id"]) if event.get("tenant_id") else UUID(int=0),
            trace_id=trace_id,
            service_name="event_dispatcher",
            event_type="event_handler_failed",
            message=f"Handler failed for {event_type}: {exc}",
            context={"event_id": event_id, "error": str(exc), "worker_id": worker_id},
            log_level="error",
        )

        return {
            "event_id": event_id,
            "event_type": event_type,
            "status": "failed",
            "trace_id": trace_id,
            "error": str(exc),
        }


def _handler_succeeded(result: Any) -> bool:
    if not isinstance(result, dict):
        return True
    if result.get("status") in _TERMINAL_FAILURE_STATUSES:
        return False
    if result.get("outcome") == "failed":
        return False
    tool_outcome = result.get("tool_broker_outcome")
    if isinstance(tool_outcome, dict) and tool_outcome.get("outcome") == "failed":
        return False
    return True


def _handler_error_message(result: Any) -> str:
    if isinstance(result, dict):
        if result.get("error"):
            return str(result["error"])
        tool_outcome = result.get("tool_broker_outcome")
        if isinstance(tool_outcome, dict) and tool_outcome.get("error"):
            return str(tool_outcome["error"])
    return "Handler returned an unsuccessful result"


def _mark_processed(event_id: str) -> None:
    """Mark an event as processed."""
    sb = _get_supabase()
    if not sb:
        return
    try:
        sb.table("events").update({
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "status": "processed",
            "claimed_by": None,
            "claimed_at": None,
            "last_error": None,
            "next_attempt_at": None,
        }).eq("id", event_id).execute()
    except Exception as exc:
        logger.warning("Failed to mark event %s as processed: %s", event_id, exc)


def _mark_failed(event: dict[str, Any], error: str) -> None:
    """Mark an event as failed or dead-lettered."""
    retry_count = int(event.get("retry_count") or 1)
    max_retries = int(event.get("max_retries") or 5)
    if retry_count >= max_retries:
        _mark_dead_letter(event, error)
        return

    backoff_seconds = min(60 * (2 ** max(retry_count - 1, 0)), 3600)
    next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
    sb = _get_supabase()
    if not sb:
        return
    try:
        sb.table("events").update({
            "status": "failed",
            "claimed_by": None,
            "claimed_at": None,
            "last_error": error[:2000],
            "next_attempt_at": next_attempt_at.isoformat(),
        }).eq("id", event.get("id")).execute()
    except Exception as exc:
        logger.warning("Failed to mark event %s as failed: %s", event.get("id"), exc)


def _mark_dead_letter(event: dict[str, Any], error: str) -> None:
    sb = _get_supabase()
    if not sb:
        return
    try:
        sb.table("events").update({
            "status": "dead_letter",
            "claimed_by": None,
            "claimed_at": None,
            "last_error": error[:2000],
            "dead_lettered_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", event.get("id")).execute()
    except Exception as exc:
        logger.warning("Failed to dead-letter event %s: %s", event.get("id"), exc)
