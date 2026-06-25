"""Trace ID propagation — ensure every record carries a trace_id.

Chapter 18.1: All records (Event, WorkflowRun, WorkflowStepLog, ActionProposal,
ApprovalRequest, ActionExecution, AgentRun, SpawnContract, Lead, Quote, Job,
MessageDraft) must carry trace_id. Generate at entry if missing, propagate
through all created records.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


def _table_admin(name: str):
    from chromagora_api.db.tenant import get_backend_supabase

    return get_backend_supabase().table(name)


def ensure_trace_id(trace_id: Optional[str] = None) -> str:
    """Return the given trace_id or generate a new one."""
    return trace_id or str(uuid4())


def log_structured_event(
    tenant_id: UUID,
    trace_id: str,
    service_name: str,
    event_type: str,
    message: str = "",
    log_level: str = "info",
    context: Optional[dict[str, Any]] = None,
) -> None:
    """Write a structured log entry to the structured_logs table.

    Best-effort: never raises. Logs locally on DB failure.
    """
    try:
        payload = {
            "tenant_id": str(tenant_id),
            "trace_id": trace_id,
            "service_name": service_name,
            "log_level": log_level,
            "event_type": event_type,
            "message": message,
            "context_json": context or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _table_admin("structured_logs").insert(payload).execute()
    except Exception:
        logger.debug(
            "Failed to write structured log: trace_id=%s service=%s event=%s",
            trace_id,
            service_name,
            event_type,
            exc_info=True,
        )


def propagate_trace_to_workflow_step(
    workflow_run_id: UUID,
    trace_id: str,
) -> None:
    """Ensure a workflow step log inherits the parent workflow's trace_id."""
    try:
        _table_admin("workflow_step_logs").update({"trace_id": trace_id}).eq(
            "workflow_run_id", str(workflow_run_id)
        ).eq("trace_id", None).execute()
    except Exception:
        logger.debug(
            "Failed to propagate trace to workflow steps: run_id=%s",
            workflow_run_id,
            exc_info=True,
        )


def propagate_trace_to_agent_run(
    agent_run_id: UUID,
    trace_id: str,
) -> None:
    """Ensure an agent run record carries the trace_id."""
    try:
        _table_admin("agent_runs").update({"trace_id": trace_id}).eq(
            "id", str(agent_run_id)
        ).eq("trace_id", None).execute()
    except Exception:
        logger.debug(
            "Failed to propagate trace to agent_run: run_id=%s",
            agent_run_id,
            exc_info=True,
        )


def get_records_by_trace(trace_id: str) -> dict[str, list[dict]]:
    """Retrieve all records associated with a trace_id across all tables.

    Returns a dict of table_name -> list of matching records.
    Useful for debugging and observability.
    """
    from chromagora_api.db.tenant import (
        DatabaseUnavailable,
        TenantError,
        get_active_business_ids,
        get_active_tenant_id,
        get_backend_supabase,
    )
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
        business_ids = get_active_business_ids(sb)
    except (RuntimeError, TenantError, DatabaseUnavailable):
        return {}

    tables = [
        "events",
        "workflow_runs",
        "workflow_step_logs",
        "action_proposals",
        "approval_requests",
        "action_executions",
        "agent_runs",
        "spawn_contracts",
        "leads",
        "quotes",
        "jobs",
        "message_drafts",
        "structured_logs",
    ]

    results: dict[str, list[dict]] = {}
    tenant_scoped_tables = {
        "events",
        "workflow_runs",
        "action_proposals",
        "approval_requests",
        "action_executions",
        "agent_runs",
        "structured_logs",
    }
    business_scoped_tables = {"leads", "quotes", "jobs", "message_drafts", "spawn_contracts"}
    for table in tables:
        try:
            if table == "workflow_step_logs":
                run_resp = (
                    sb.table("workflow_runs")
                    .select("id")
                    .eq("tenant_id", tenant_id)
                    .execute()
                )
                run_ids = [row["id"] for row in (run_resp.data or [])]
                if not run_ids:
                    continue
                resp = (
                    sb.table(table)
                    .select("*")
                    .eq("trace_id", trace_id)
                    .in_("workflow_run_id", run_ids)
                    .execute()
                )
                if resp.data:
                    results[table] = resp.data
                continue
            query = sb.table(table).select("*").eq("trace_id", trace_id)
            if table in tenant_scoped_tables:
                query = query.eq("tenant_id", tenant_id)
            elif table in business_scoped_tables:
                if not business_ids:
                    continue
                query = query.in_("business_id", business_ids)
            resp = query.execute()
            if resp.data:
                results[table] = resp.data
        except Exception:
            logger.debug("Failed to query trace on table %s", table, exc_info=True)

    return results
