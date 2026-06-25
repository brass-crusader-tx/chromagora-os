"""Agent Run management."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_schemas.agents import (
    AgentRunCreate,
    AgentRunResponse,
    AgentRunStatus,
)

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


def _table_admin(name: str):
    return _get_supabase().table(name)


def _ensure_business_scope(sb, business_id: UUID, tenant_id: UUID | None = None) -> None:
    from chromagora_api.db.tenant import get_business_tenant_id

    scoped_tenant_id = get_business_tenant_id(str(business_id), sb)
    if not scoped_tenant_id:
        raise RuntimeError("Business not found")
    if tenant_id and scoped_tenant_id != str(tenant_id):
        raise RuntimeError("Business not found")


def start_agent_run(
    tenant_id: UUID,
    data: AgentRunCreate,
) -> Optional[AgentRunResponse]:
    """Start a new agent run."""
    sb = _get_supabase()
    if not sb:
        return None
    _ensure_business_scope(sb, data.business_id, tenant_id)

    trace_id = str(uuid4())
    payload = {
        "tenant_id": str(tenant_id),
        "business_id": str(data.business_id),
        "agent_instance_id": str(data.agent_instance_id) if data.agent_instance_id else None,
        "agent_type": data.agent_type,
        "trigger_type": data.trigger_type,
        "trigger_event_id": str(data.trigger_event_id) if data.trigger_event_id else None,
        "workflow_run_id": str(data.workflow_run_id) if data.workflow_run_id else None,
        "status": AgentRunStatus.RUNNING.value,
        "input_json": data.input_json,
        "trace_id": trace_id,
    }
    resp = _table_admin("agent_runs").insert(payload).execute()
    if not resp.data:
        return None
    return AgentRunResponse(**resp.data[0])


def complete_agent_run(
    run_id: UUID,
    output_json: Optional[dict] = None,
    cost_estimate: Optional[float] = None,
    model_name: Optional[str] = None,
    model_tier: Optional[int] = None,
) -> Optional[AgentRunResponse]:
    """Mark an agent run as completed."""
    update_data: dict[str, Any] = {
        "status": AgentRunStatus.COMPLETED.value,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    if output_json is not None:
        update_data["output_json"] = output_json
    if cost_estimate is not None:
        update_data["cost_estimate"] = cost_estimate
    if model_name is not None:
        update_data["model_name"] = model_name
    if model_tier is not None:
        update_data["model_tier"] = model_tier

    resp = (
        _table_admin("agent_runs")
        .update(update_data)
        .eq("id", str(run_id))
        .execute()
    )
    if not resp.data:
        return None
    return AgentRunResponse(**resp.data[0])


def fail_agent_run(
    run_id: UUID,
    error_message: str = "Unknown error",
) -> Optional[AgentRunResponse]:
    """Mark an agent run as failed."""
    update_data: dict[str, Any] = {
        "status": AgentRunStatus.FAILED.value,
        "error_message": error_message,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    resp = (
        _table_admin("agent_runs")
        .update(update_data)
        .eq("id", str(run_id))
        .execute()
    )
    if not resp.data:
        return None
    return AgentRunResponse(**resp.data[0])


def list_agent_runs(business_id: UUID) -> list[dict]:
    """List agent runs for a business."""
    sb = _get_supabase()
    if not sb:
        return []
    _ensure_business_scope(sb, business_id)
    resp = (
        sb.table("agent_runs")
        .select("*")
        .eq("business_id", str(business_id))
        .order("started_at", desc=True)
        .limit(50)
        .execute()
    )
    return resp.data or []
