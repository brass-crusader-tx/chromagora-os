"""Workflow-lite engine — database-backed workflow execution."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from chromagora_schemas.workflows import (
    WorkflowRunCreate,
    WorkflowRunResponse,
    WorkflowStatus,
    WorkflowStepLogCreate,
    WorkflowStepLogResponse,
    WorkflowStepStatus,
)

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase
    return get_backend_supabase()


def _table_admin(name: str):
    return _get_supabase().table(name)


def _active_tenant_id(sb) -> str:
    from chromagora_api.db.tenant import get_active_tenant_id

    return get_active_tenant_id(sb)


def _ensure_business_scope(sb, business_id: UUID, tenant_id: UUID | None = None) -> str:
    from chromagora_api.db.tenant import get_business_tenant_id

    scoped_tenant_id = get_business_tenant_id(str(business_id), sb)
    if not scoped_tenant_id:
        raise RuntimeError("Business not found")
    if tenant_id and scoped_tenant_id != str(tenant_id):
        raise RuntimeError("Business not found")
    return scoped_tenant_id


def _ensure_workflow_run_scope(sb, workflow_run_id: UUID) -> str:
    tenant_id = _active_tenant_id(sb)
    resp = (
        sb.table("workflow_runs")
        .select("tenant_id")
        .eq("id", str(workflow_run_id))
        .eq("tenant_id", tenant_id)
        .execute()
    )
    if not resp.data:
        raise RuntimeError("Workflow not found")
    return tenant_id


# ---------------------------------------------------------------------------
# Core CRUD
# ---------------------------------------------------------------------------

def create_workflow_run(
    tenant_id: UUID,
    data: WorkflowRunCreate,
) -> Optional[WorkflowRunResponse]:
    """Create a new workflow run."""
    sb = _get_supabase()
    _ensure_business_scope(sb, data.business_id, tenant_id)
    payload = {
        "tenant_id": str(tenant_id),
        "business_id": str(data.business_id),
        "workflow_type": data.workflow_type,
        "workflow_definition_id": str(data.workflow_definition_id) if data.workflow_definition_id else None,
        "input_json": data.input_json,
        "correlation_id": str(data.correlation_id) if data.correlation_id else None,
        "trace_id": data.trace_id or str(uuid4()),
        "status": WorkflowStatus.PENDING.value,
    }
    resp = sb.table("workflow_runs").insert(payload).execute()
    if not resp.data:
        return None
    return WorkflowRunResponse(**resp.data[0])


def log_workflow_step(
    workflow_run_id: UUID,
    data: WorkflowStepLogCreate,
) -> Optional[WorkflowStepLogResponse]:
    """Log a workflow step execution."""
    sb = _get_supabase()
    _ensure_workflow_run_scope(sb, workflow_run_id)
    payload = {
        "workflow_run_id": str(workflow_run_id),
        "step_name": data.step_name,
        "status": data.status.value,
        "input_json": data.input_json,
        "output_json": data.output_json,
        "error_message": data.error_message,
    }
    resp = sb.table("workflow_step_logs").insert(payload).execute()
    if not resp.data:
        return None
    return WorkflowStepLogResponse(**resp.data[0])


def update_workflow_state(
    workflow_run_id: UUID,
    status: WorkflowStatus,
    current_step: Optional[str] = None,
    state_json: Optional[dict] = None,
    result_json: Optional[dict] = None,
) -> Optional[WorkflowRunResponse]:
    """Update workflow run status and state."""
    sb = _get_supabase()
    tenant_id = _ensure_workflow_run_scope(sb, workflow_run_id)
    update_data: dict[str, Any] = {
        "status": status.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if current_step is not None:
        update_data["current_step"] = current_step
    if state_json is not None:
        update_data["state_json"] = state_json
    if result_json is not None:
        update_data["result_json"] = result_json

    resp = (
        sb.table("workflow_runs")
        .update(update_data)
        .eq("id", str(workflow_run_id))
        .eq("tenant_id", tenant_id)
        .execute()
    )
    if not resp.data:
        return None
    return WorkflowRunResponse(**resp.data[0])


def mark_waiting_for_approval(workflow_run_id: UUID) -> Optional[WorkflowRunResponse]:
    """Mark a workflow as waiting for approval."""
    return update_workflow_state(workflow_run_id, WorkflowStatus.WAITING_FOR_APPROVAL)


def complete_workflow(
    workflow_run_id: UUID,
    result_json: Optional[dict] = None,
) -> Optional[WorkflowRunResponse]:
    """Mark a workflow as completed."""
    sb = _get_supabase()
    tenant_id = _ensure_workflow_run_scope(sb, workflow_run_id)
    update_data: dict[str, Any] = {
        "status": WorkflowStatus.COMPLETED.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    if result_json is not None:
        update_data["result_json"] = result_json

    resp = (
        sb.table("workflow_runs")
        .update(update_data)
        .eq("id", str(workflow_run_id))
        .eq("tenant_id", tenant_id)
        .execute()
    )
    if not resp.data:
        return None
    return WorkflowRunResponse(**resp.data[0])


def fail_workflow(
    workflow_run_id: UUID,
    error_message: str = "Unknown error",
) -> Optional[WorkflowRunResponse]:
    """Mark a workflow as failed."""
    sb = _get_supabase()
    tenant_id = _ensure_workflow_run_scope(sb, workflow_run_id)
    update_data: dict[str, Any] = {
        "status": WorkflowStatus.FAILED.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "state_json": {"error": error_message},
    }

    resp = (
        sb.table("workflow_runs")
        .update(update_data)
        .eq("id", str(workflow_run_id))
        .eq("tenant_id", tenant_id)
        .execute()
    )
    if not resp.data:
        return None
    return WorkflowRunResponse(**resp.data[0])
