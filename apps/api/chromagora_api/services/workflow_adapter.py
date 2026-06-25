"""Workflow engine adapter interface.

Defines the contract that workflow implementations must satisfy.
Current adapter: WorkflowLiteAdapter (database-backed).
Future adapter: TemporalAdapter (documented, not implemented — see Chapter 21).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class WorkflowAdapter(ABC):
    """Abstract interface for workflow execution engines."""

    @abstractmethod
    def start_workflow(
        self,
        workflow_type: str,
        business_id: UUID,
        input_data: dict[str, Any],
        correlation_id: Optional[UUID] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        """Start a workflow. Returns the workflow run ID."""
        ...

    @abstractmethod
    def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        signal_data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Send a signal to a running workflow."""
        ...

    @abstractmethod
    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get current workflow status and state."""
        ...

    @abstractmethod
    def cancel_workflow(self, workflow_id: str, reason: str = "cancelled") -> bool:
        """Cancel a running workflow."""
        ...


class WorkflowLiteAdapter(WorkflowAdapter):
    """Database-backed workflow adapter (current implementation)."""

    def start_workflow(
        self,
        workflow_type: str,
        business_id: UUID,
        input_data: dict[str, Any],
        correlation_id: Optional[UUID] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        from chromagora_api.services.workflow_engine import create_workflow_run
        from chromagora_schemas.workflows import WorkflowRunCreate

        # Import tenant context — in production this comes from request context
        tenant_id = input_data.pop("_tenant_id", None)
        if not tenant_id:
            raise ValueError("tenant_id required in input_data")

        run_create = WorkflowRunCreate(
            business_id=business_id,
            workflow_type=workflow_type,
            input_json=input_data,
            correlation_id=correlation_id,
            trace_id=trace_id,
        )
        result = create_workflow_run(tenant_id, run_create)
        if not result:
            raise RuntimeError("Failed to create workflow run")
        return str(result.id)

    def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        signal_data: Optional[dict[str, Any]] = None,
    ) -> bool:
        from chromagora_api.services.workflow_engine import update_workflow_state
        from chromagora_schemas.workflows import WorkflowStatus

        # Map signal names to status transitions
        signal_map = {
            "approve": WorkflowStatus.RUNNING,
            "reject": WorkflowStatus.CANCELLED,
            "cancel": WorkflowStatus.CANCELLED,
        }
        status = signal_map.get(signal_name)
        if not status:
            logger.warning("Unknown signal: %s", signal_name)
            return False

        result = update_workflow_state(
            UUID(workflow_id),
            status=status,
            state_json={"last_signal": signal_name, **(signal_data or {})},
        )
        return result is not None

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_tenant_id, get_backend_supabase

        try:
            sb = get_backend_supabase()
            tenant_id = get_active_tenant_id(sb)
        except (RuntimeError, DatabaseUnavailable):
            return {"error": "Database not configured"}

        resp = (
            sb.table("workflow_runs")
            .select("id, status, current_step, state_json, result_json, started_at, completed_at, updated_at")
            .eq("id", workflow_id)
            .eq("tenant_id", tenant_id)
            .execute()
        )
        if not resp.data:
            return {"error": "Workflow not found"}
        return resp.data[0]

    def cancel_workflow(self, workflow_id: str, reason: str = "cancelled") -> bool:
        from chromagora_api.services.workflow_engine import update_workflow_state
        from chromagora_schemas.workflows import WorkflowStatus

        result = update_workflow_state(
            UUID(workflow_id),
            status=WorkflowStatus.CANCELLED,
            state_json={"cancel_reason": reason},
        )
        return result is not None


# ---------------------------------------------------------------------------
# TemporalAdapter — Documented but NOT implemented.
# Requires Temporal Cloud and Python SDK. See docs/TEMPORAL_UPGRADE_PLAN.md.
# ---------------------------------------------------------------------------

# class TemporalAdapter(WorkflowAdapter):
#     """Temporal Cloud-backed workflow adapter.
#
#     NOT IMPLEMENTED in v0.1.
#     Requires: temporalio, Temporal Cloud account, namespace configuration.
#
#     Migration steps:
#     1. Install temporalio: pip install temporalio
#     2. Configure TEMPORAL_CLOUD_URL, TEMPORAL_NAMESPACE, TEMPORAL_TASK_QUEUE
#     3. Implement workflow classes as Python functions decorated with @workflow.defn
#     4. Implement activity classes for Tool Broker calls
#     5. Start Temporal Worker as a separate process
#     6. Route through this adapter instead of WorkflowLiteAdapter
#     """
#
#     def start_workflow(self, workflow_type, business_id, input_data, **kwargs):
#         # Connect to Temporal Cloud and start workflow
#         ...
#
#     def signal_workflow(self, workflow_id, signal_name, signal_data=None):
#         # Signal running workflow
#         ...
#
#     def get_workflow_status(self, workflow_id):
#         # Query workflow state
#         ...
#
#     def cancel_workflow(self, workflow_id, reason="cancelled"):
#         # Cancel workflow execution
#         ...


def get_adapter() -> WorkflowAdapter:
    """Get the current workflow adapter. Defaults to WorkflowLiteAdapter."""
    # Future: check feature flag for USE_TEMPORAL
    return WorkflowLiteAdapter()
