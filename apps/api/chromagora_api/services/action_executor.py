"""Action execution service — performs approved actions.

For v0.1, supported execution modes:
- create_task: creates a CRM task in crm_tasks table
- create_message_draft: creates a message draft in message_drafts table
- internal_update: updates quote/customer state

Does NOT perform external sending (no real email/SMS adapters yet).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_api.services.trace_propagation import ensure_trace_id, log_structured_event
from chromagora_api.services.runtime_utils import parse_json_field, to_jsonable

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


def _validate_approval_request(sb, approval_request_id: UUID, action_proposal_id: UUID) -> Optional[dict[str, Any]]:
    """Return an error result if the approval request is not approved for this proposal."""
    try:
        resp = sb.table("approval_requests").select("*").eq("id", str(approval_request_id)).execute()
        if not resp.data:
            return {"status": "failed", "error": "Approval request not found"}
        approval = resp.data[0]
    except Exception as exc:
        return {"status": "failed", "error": f"Failed to load approval request: {exc}"}

    if approval.get("action_proposal_id") != str(action_proposal_id):
        return {"status": "failed", "error": "Approval request does not match proposal"}
    if approval.get("status") != "approved":
        return {"status": "failed", "error": f"Approval request is in state '{approval.get('status')}'"}
    return None


def _find_existing_execution(sb, tenant_id: str | None, idempotency_key: str) -> Optional[dict[str, Any]]:
    try:
        query = sb.table("action_executions").select("*").eq("idempotency_key", idempotency_key)
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        resp = query.limit(1).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def _find_existing_record(sb, table: str, idempotency_key: str) -> Optional[dict[str, Any]]:
    try:
        resp = sb.table(table).select("*").eq("idempotency_key", idempotency_key).limit(1).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def execute_approved_action(
    action_proposal_id: UUID,
    approval_request_id: Optional[UUID] = None,
    trace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Execute an approved action proposal.

    Creates the appropriate internal record (task or draft),
    updates quote state, emits follow-up events.

    Returns the execution result.
    """
    sb = _get_supabase()
    if not sb:
        return {"status": "failed", "error": "Database unavailable"}

    if not trace_id:
        trace_id = ensure_trace_id()

    # Load the action proposal
    try:
        resp = sb.table("action_proposals").select("*").eq("id", str(action_proposal_id)).execute()
        if not resp.data:
            return {"status": "failed", "error": "Action proposal not found"}
        proposal = resp.data[0]
    except Exception as exc:
        return {"status": "failed", "error": f"Failed to load proposal: {exc}"}

    # State machine: execution is only allowed after an explicit approval state.
    proposal_status = proposal.get("status", "")
    if proposal_status != "approved":
        return {"status": "failed", "error": f"Proposal in state '{proposal_status}' cannot be executed"}

    tenant_id = proposal.get("tenant_id")
    business_id = proposal.get("business_id")
    action_type = proposal.get("action_type", "")
    proposed_payload = parse_json_field(proposal.get("proposed_payload", {}), default={})
    quote_id = proposal.get("quote_id")
    customer_id = proposal.get("customer_id")
    agent_run_id = proposal.get("agent_run_id")

    if approval_request_id:
        approval_check = _validate_approval_request(sb, approval_request_id, action_proposal_id)
        if approval_check:
            return approval_check

    execution_idempotency_key = f"action.execute:{action_proposal_id}"
    existing_execution = _find_existing_execution(sb, tenant_id, execution_idempotency_key)
    if existing_execution:
        result_json = parse_json_field(existing_execution.get("result_json"), default={})
        if existing_execution.get("result_status") == "success" and isinstance(result_json, dict):
            return {**result_json, "duplicate": True, "execution_id": existing_execution.get("id"), "trace_id": trace_id}
        return {
            "status": "failed",
            "duplicate": True,
            "execution_id": existing_execution.get("id"),
            "error": f"Existing execution is in state {existing_execution.get('result_status')}",
            "trace_id": trace_id,
        }

    # Determine execution mode
    execution_mode = _map_action_type_to_execution_mode(action_type)

    # Create execution record
    execution_id = str(uuid4())
    try:
        sb.table("action_executions").insert({
            "id": execution_id,
            "tenant_id": tenant_id,
            "business_id": business_id,
            "action_proposal_id": str(action_proposal_id),
            "approval_request_id": str(approval_request_id) if approval_request_id else None,
            "tool_name": action_type,
            "tool_action": execution_mode,
            "result_status": "running",
            "executed_by_type": "system",
            "executed_by_id": None,
            "execution_mode": execution_mode,
            "idempotency_key": execution_idempotency_key,
            "trace_id": trace_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as exc:
        existing_execution = _find_existing_execution(sb, tenant_id, execution_idempotency_key)
        if existing_execution:
            result_json = parse_json_field(existing_execution.get("result_json"), default={})
            if existing_execution.get("result_status") == "success" and isinstance(result_json, dict):
                return {**result_json, "duplicate": True, "execution_id": existing_execution.get("id"), "trace_id": trace_id}
            return {
                "status": "failed",
                "duplicate": True,
                "execution_id": existing_execution.get("id"),
                "error": f"Existing execution is in state {existing_execution.get('result_status')}",
                "trace_id": trace_id,
            }
        logger.error("Failed to create execution record: %s", exc)

    # Execute based on mode
    result = {"status": "failed", "error": "Unknown execution mode"}
    created_record_id = None

    try:
        if execution_mode == "create_task":
            result, created_record_id = _execute_create_task(
                sb, tenant_id, business_id, quote_id, customer_id,
                agent_run_id, action_proposal_id, approval_request_id,
                proposed_payload, trace_id, f"crm_task:{action_proposal_id}",
            )
        elif execution_mode == "create_message_draft":
            result, created_record_id = _execute_create_message_draft(
                sb, tenant_id, business_id, quote_id, customer_id,
                agent_run_id, action_proposal_id, approval_request_id,
                proposed_payload, trace_id, f"message_draft:{action_proposal_id}",
            )
        elif execution_mode == "internal_update":
            result = _execute_internal_update(
                sb, tenant_id, business_id, quote_id, proposed_payload, trace_id,
            )
        else:
            result = {"status": "failed", "error": f"Unsupported execution mode: {execution_mode}"}
    except Exception as exc:
        logger.exception("Execution failed: %s", exc)
        result = {"status": "failed", "error": str(exc)}

    # Update execution record with result
    try:
        sb.table("action_executions").update({
            "result_status": result.get("status", "failed"),
            "result_json": to_jsonable(result),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", execution_id).execute()
    except Exception as exc:
        logger.warning("Failed to update execution record: %s", exc)

    # If execution succeeded, update state and emit events
    if result.get("status") == "success" and quote_id:
        _update_quote_after_follow_up(
            sb, tenant_id, business_id, quote_id, action_type, trace_id,
        )
        _emit_follow_up_events(
            sb, tenant_id, business_id, quote_id, action_type,
            action_proposal_id, execution_id, result, trace_id,
        )

    # Update proposal status according to execution result.
    try:
        if result.get("status") == "success":
            sb.table("action_proposals").update({
                "status": "executed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", str(action_proposal_id)).execute()
        else:
            sb.table("action_proposals").update({
                "status": "failed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", str(action_proposal_id)).execute()
    except Exception:
        pass

    result["execution_id"] = execution_id
    result["trace_id"] = trace_id
    if created_record_id:
        result["created_record_id"] = created_record_id

    return result


def _map_action_type_to_execution_mode(action_type: str) -> str:
    """Map action type to execution mode."""
    mapping = {
        "create_quote_follow_up_task": "create_task",
        "create_quote_follow_up_draft": "create_message_draft",
        "send_quote_follow_up": "send_message",  # blocked — no real adapter
        "create_task": "create_task",
        "create_message_draft": "create_message_draft",
        "memo": "internal_update",
    }
    return mapping.get(action_type, "internal_update")


# ---------------------------------------------------------------------------
# Execution implementations
# ---------------------------------------------------------------------------

def _execute_create_task(
    sb, tenant_id, business_id, quote_id, customer_id,
    agent_run_id, action_proposal_id, approval_request_id,
    payload: dict, trace_id: str, idempotency_key: str,
) -> tuple[dict, Optional[str]]:
    """Create a CRM task idempotently."""
    existing = _find_existing_record(sb, "crm_tasks", idempotency_key)
    if existing:
        return {"status": "success", "task_id": existing.get("id"), "mode": "create_task", "duplicate": True}, existing.get("id")

    task_id = str(uuid4())
    try:
        sb.table("crm_tasks").insert({
            "id": task_id,
            "tenant_id": tenant_id,
            "business_id": business_id,
            "quote_id": quote_id,
            "customer_id": customer_id,
            "agent_run_id": agent_run_id,
            "action_proposal_id": str(action_proposal_id),
            "approval_request_id": str(approval_request_id) if approval_request_id else None,
            "title": payload.get("title", "Follow up on sent quote"),
            "description": payload.get("description", ""),
            "due_at": payload.get("due_at"),
            "status": "open",
            "source": "agent",
            "trace_id": trace_id,
            "idempotency_key": idempotency_key,
        }).execute()
    except Exception as exc:
        return {"status": "failed", "error": f"Task creation failed: {exc}"}, None

    return {"status": "success", "task_id": task_id, "mode": "create_task"}, task_id


def _execute_create_message_draft(
    sb, tenant_id, business_id, quote_id, customer_id,
    agent_run_id, action_proposal_id, approval_request_id,
    payload: dict, trace_id: str, idempotency_key: str,
) -> tuple[dict, Optional[str]]:
    """Create a message draft idempotently."""
    existing = _find_existing_record(sb, "message_drafts", idempotency_key)
    if existing:
        return {"status": "success", "draft_id": existing.get("id"), "mode": "create_message_draft", "duplicate": True}, existing.get("id")

    draft_id = str(uuid4())
    # Build insert with only columns that exist in the current schema.
    # Migration 000024 adds tenant_id, quote_id, customer_id, agent_run_id,
    # approval_request_id, source — those are included when the schema supports them.
    draft_data: dict[str, Any] = {
        "id": draft_id,
        "business_id": business_id,
        "body": payload.get("body", ""),
        "status": "draft",
        "trace_id": trace_id,
    }
    # Optional columns — only include if the target table has them.
    for col, val in [
        ("tenant_id", tenant_id),
        ("quote_id", quote_id),
        ("customer_id", customer_id),
        ("agent_run_id", agent_run_id),
        ("approval_request_id", str(approval_request_id) if approval_request_id else None),
        ("source", "agent"),
        ("channel", payload.get("channel", "email")),
        ("recipient", payload.get("recipient", "")),
        ("subject", payload.get("subject")),
        ("related_action_proposal_id", str(action_proposal_id)),
        ("idempotency_key", idempotency_key),
    ]:
        if val is not None:
            draft_data[col] = val

    try:
        sb.table("message_drafts").insert(draft_data).execute()
    except Exception as exc:
        return {"status": "failed", "error": f"Draft creation failed: {exc}"}, None

    return {"status": "success", "draft_id": draft_id, "mode": "create_message_draft"}, draft_id


def _execute_internal_update(
    sb, tenant_id, business_id, quote_id,
    payload: dict, trace_id: str,
) -> dict:
    """Perform internal state update (e.g., quote status change)."""
    if not quote_id:
        return {"status": "failed", "error": "No quote_id for internal update"}

    update_fields = {}
    if "status" in payload:
        update_fields["status"] = payload["status"]
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        sb.table("quotes").update(update_fields).eq("id", quote_id).execute()
    except Exception as exc:
        return {"status": "failed", "error": f"Quote update failed: {exc}"}

    return {"status": "success", "mode": "internal_update"}


# ---------------------------------------------------------------------------
# State mutation after execution
# ---------------------------------------------------------------------------

def _update_quote_after_follow_up(
    sb, tenant_id, business_id, quote_id,
    action_type: str, trace_id: str,
) -> None:
    """Update quote state after a successful follow-up execution."""
    now = datetime.now(timezone.utc)

    # Load current quote to calculate next follow-up
    try:
        resp = sb.table("quotes").select("follow_up_count, status").eq("id", quote_id).execute()
        if not resp.data:
            return
        quote = resp.data[0]
    except Exception:
        # follow_up_count column may not exist yet (pre-migration 24)
        return

    current_count = quote.get("follow_up_count") or 0
    new_count = current_count + 1

    # Load max follow-ups from business preferences
    max_follow_ups = 3
    try:
        pref_resp = (
            sb.table("business_preferences")
            .select("value_json")
            .eq("business_id", business_id)
            .eq("key", "max_quote_follow_ups")
            .execute()
        )
        if pref_resp.data:
            val = pref_resp.data[0].get("value_json", {})
            if isinstance(val, dict) and "value" in val:
                max_follow_ups = val["value"]
            elif isinstance(val, int):
                max_follow_ups = val
    except Exception:
        pass

    # Determine the new quote status
    # If a task was created, the follow-up is pending until the task is completed
    # If a draft was created, the follow-up has been proposed and is pending approval already
    if action_type in ("create_quote_follow_up_task", "create_task"):
        new_status = "follow_up_pending"
    else:
        new_status = "followed_up"

    update_data: dict[str, Any] = {
        "follow_up_count": new_count,
        "last_followup_at": now.isoformat(),
        "status": new_status,
        "updated_at": now.isoformat(),
    }

    # Calculate next follow-up if not at max
    if new_count < max_follow_ups:
        # Default: follow up again in 3 days, independently configurable
        # from initial stale detection.
        interval_days = 3
        try:
            pref_resp = (
                sb.table("business_preferences")
                .select("key, value_json")
                .eq("business_id", business_id)
                .in_("key", ["follow_up_interval_days", "stale_quote_threshold_days"])
                .execute()
            )
            for pref in pref_resp.data or []:
                val = pref.get("value_json", {})
                if isinstance(val, dict) and "value" in val:
                    pref_value = val["value"]
                elif isinstance(val, int):
                    pref_value = val
                else:
                    continue
                interval_days = pref_value
                if pref.get("key") == "follow_up_interval_days":
                    break
        except Exception:
            pass
        update_data["next_follow_up_at"] = (now + timedelta(days=interval_days)).isoformat()
    else:
        update_data["next_follow_up_at"] = None

    try:
        sb.table("quotes").update(update_data).eq("id", quote_id).execute()
    except Exception as exc:
        logger.error("Failed to update quote after follow-up: %s", exc)

    # Emit quote.status_changed event
    try:
        sb.table("events").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": business_id,
            "event_type": "quote.status_changed",
            "source_type": "execution",
            "source_id": quote_id,
            "entity_type": "quote",
            "entity_id": quote_id,
            "payload_json": {
                "quote_id": quote_id,
                "old_status": quote.get("status"),
                "new_status": new_status,
                "follow_up_count": new_count,
            },
            "trace_id": trace_id,
        }).execute()
    except Exception:
        pass


def _emit_follow_up_events(
    sb, tenant_id, business_id, quote_id,
    action_type, action_proposal_id, execution_id,
    result: dict, trace_id: str,
) -> None:
    """Emit follow-up events after successful execution."""
    event_type = "quote.follow_up_executed"
    payload = {
        "quote_id": quote_id,
        "action_type": action_type,
        "action_proposal_id": str(action_proposal_id),
        "execution_id": execution_id,
        "result_status": result.get("status"),
    }

    try:
        sb.table("events").insert({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "business_id": business_id,
            "event_type": event_type,
            "source_type": "execution",
            "source_id": str(action_proposal_id),
            "entity_type": "quote",
            "entity_id": quote_id,
            "payload_json": payload,
            "trace_id": trace_id,
        }).execute()
    except Exception as exc:
        logger.warning("Failed to emit %s event: %s", event_type, exc)

    # Also write to action_ledger via structured_logs
    try:
        log_structured_event(
            tenant_id=UUID(tenant_id) if tenant_id else UUID(int=0),
            trace_id=trace_id,
            service_name="action_execution",
            event_type=event_type,
            message=f"Executed {action_type} for quote {quote_id}",
            context=payload,
        )
    except Exception:
        pass
