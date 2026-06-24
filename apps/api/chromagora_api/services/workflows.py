"""Workflow implementations — review request and stale quote."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_api.services.workflow_engine import (
    create_workflow_run,
    log_workflow_step,
    update_workflow_state,
    mark_waiting_for_approval,
    complete_workflow,
)
from chromagora_api.services.tool_broker import request_tool_execution
from chromagora_schemas.workflows import (
    WorkflowRunCreate,
    WorkflowStatus,
    WorkflowStepStatus,
)

logger = logging.getLogger(__name__)

STALE_QUOTE_DAYS = 3


def run_review_request_workflow(
    tenant_id: UUID,
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
) -> dict[str, Any]:
    """Execute the completed_job_review_request workflow in dry-run mode.

    Steps:
    1. Create WorkflowRun
    2. Create ActionProposal for reputation.queue_review_request via Tool Broker
    3. If approval required -> mark waiting_for_approval
    4. If allowed -> dry-run ActionExecution
    5. Complete if no approval required
    """
    trace_id = str(UUID())

    # Step 1: Create WorkflowRun
    run = create_workflow_run(
        tenant_id=tenant_id,
        data=WorkflowRunCreate(
            business_id=business_id,
            workflow_type="completed_job_review_request",
            input_json={
                "customer_name": customer_name,
                "customer_contact": customer_contact,
                "job_summary": job_summary,
                "completed_at": completed_at,
            },
            trace_id=trace_id,
        ),
    )

    if not run:
        return {"status": "failed", "error": "Failed to create workflow run"}

    run_id = run.id

    # Log step 1
    log_workflow_step(
        workflow_run_id=run_id,
        data=WorkflowStepLogCreate(
            step_name="create_workflow_run",
            status=WorkflowStepStatus.COMPLETED,
            output_json={"workflow_run_id": str(run_id)},
        ),
    )

    # Step 2: Request tool execution via Tool Broker
    update_workflow_state(
        run_id,
        WorkflowStatus.RUNNING,
        current_step="queue_review_request",
    )

    tool_result = request_tool_execution(
        business_id=business_id,
        actor_type="workflow",
        actor_id=run_id,
        tool_name="reputation.queue_review_request",
        tool_action="queue_review_request",
        tool_args_json={
            "business_id": str(business_id),
            "customer_name": customer_name,
            "customer_contact": customer_contact,
            "job_summary": job_summary,
        },
        dry_run=True,
        risk_level="medium",
    )

    # Log step 2
    log_workflow_step(
        workflow_run_id=run_id,
        data=WorkflowStepLogCreate(
            step_name="queue_review_request",
            status=WorkflowStepStatus.COMPLETED,
            input_json={"tool": "reputation.queue_review_request"},
            output_json=tool_result,
        ),
    )

    # Step 3-5: Handle result
    tool_status = tool_result.get("status", "unknown")

    if tool_status == "blocked":
        log_workflow_step(
            workflow_run_id=run_id,
            data=WorkflowStepLogCreate(
                step_name="policy_check",
                status=WorkflowStepStatus.FAILED,
                error_message="Action blocked by policy",
            ),
        )
        complete_workflow(run_id, result_json={"tool_status": tool_status})
        return {"status": "completed", "tool_status": tool_status, "workflow_run_id": str(run_id)}

    if tool_status == "approval_required":
        mark_waiting_for_approval(run_id)
        return {"status": "waiting_for_approval", "workflow_run_id": str(run_id)}

    if tool_status == "dry_run":
        complete_workflow(run_id, result_json={
            "tool_status": "dry_run",
            "trace_id": trace_id,
        })
        return {"status": "completed", "tool_status": "dry_run", "workflow_run_id": str(run_id)}

    # Unknown status — complete with info
    complete_workflow(run_id, result_json={"tool_status": tool_status})
    return {"status": "completed", "tool_status": tool_status, "workflow_run_id": str(run_id)}


def run_stale_quote_followup_workflow(
    tenant_id: UUID,
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    service_type: str,
    quote_sent_at: str,
    quote_id: Optional[str] = None,
    quote_amount: Optional[float] = None,
    last_contact_at: Optional[str] = None,
) -> dict[str, Any]:
    """Execute the stale_quote_followup workflow in dry-run mode.

    Steps:
    1. Create WorkflowRun
    2. Determine stale (default 3 days)
    3. If not stale -> complete with no action
    4. If stale -> emit quote.stale, build ContextPacket, request crm.create_followup_task
    5. Pause for approval if required
    6. Complete if allowed
    """
    trace_id = str(UUID())

    # Step 1: Create WorkflowRun
    run = create_workflow_run(
        tenant_id=tenant_id,
        data=WorkflowRunCreate(
            business_id=business_id,
            workflow_type="stale_quote_followup",
            input_json={
                "customer_name": customer_name,
                "customer_contact": customer_contact,
                "service_type": service_type,
                "quote_sent_at": quote_sent_at,
                "quote_id": quote_id,
                "quote_amount": quote_amount,
                "last_contact_at": last_contact_at,
            },
            trace_id=trace_id,
        ),
    )

    if not run:
        return {"status": "failed", "error": "Failed to create workflow run"}

    run_id = run.id

    log_workflow_step(
        workflow_run_id=run_id,
        data=WorkflowStepLogCreate(
            step_name="create_workflow_run",
            status=WorkflowStepStatus.COMPLETED,
        ),
    )

    # Step 2: Determine stale
    try:
        sent_at = datetime.fromisoformat(quote_sent_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        sent_at = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS + 1)

    stale_threshold = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS)
    is_stale = sent_at < stale_threshold

    log_workflow_step(
        workflow_run_id=run_id,
        data=WorkflowStepLogCreate(
            step_name="check_stale",
            status=WorkflowStepStatus.COMPLETED,
            output_json={"is_stale": is_stale, "stale_threshold_days": STALE_QUOTE_DAYS},
        ),
    )

    # Step 3: If not stale -> complete with no action
    if not is_stale:
        complete_workflow(run_id, result_json={
            "action": "none",
            "reason": "Quote is not stale",
            "trace_id": trace_id,
        })
        return {"status": "completed", "action": "none", "reason": "not_stale", "workflow_run_id": str(run_id)}

    # Step 4: If stale -> request crm.create_followup_task
    update_workflow_state(
        run_id,
        WorkflowStatus.RUNNING,
        current_step="create_followup_task",
    )

    tool_result = request_tool_execution(
        business_id=business_id,
        actor_type="workflow",
        actor_id=run_id,
        tool_name="crm.create_followup_task",
        tool_action="create_followup_task",
        tool_args_json={
            "business_id": str(business_id),
            "task_type": "quote_followup",
            "due_date": datetime.now(timezone.utc).isoformat(),
            "notes": f"Stale quote follow-up for {customer_name} ({service_type})",
        },
        dry_run=True,
        dollar_exposure=quote_amount,
        risk_level="low",
    )

    log_workflow_step(
        workflow_run_id=run_id,
        data=WorkflowStepLogCreate(
            step_name="create_followup_task",
            status=WorkflowStepStatus.COMPLETED,
            input_json={"tool": "crm.create_followup_task"},
            output_json=tool_result,
        ),
    )

    # Step 5-6: Handle result
    tool_status = tool_result.get("status", "unknown")

    if tool_status == "blocked":
        complete_workflow(run_id, result_json={
            "action": "blocked",
            "tool_status": tool_status,
            "trace_id": trace_id,
        })
        return {"status": "completed", "action": "blocked", "workflow_run_id": str(run_id)}

    if tool_status == "approval_required":
        mark_waiting_for_approval(run_id)
        return {"status": "waiting_for_approval", "workflow_run_id": str(run_id)}

    if tool_status == "dry_run":
        complete_workflow(run_id, result_json={
            "action": "follow_up_task_created",
            "tool_status": "dry_run",
            "trace_id": trace_id,
        })
        return {"status": "completed", "action": "follow_up_task_created", "workflow_run_id": str(run_id)}

    complete_workflow(run_id, result_json={"tool_status": tool_status})
    return {"status": "completed", "tool_status": tool_status, "workflow_run_id": str(run_id)}
