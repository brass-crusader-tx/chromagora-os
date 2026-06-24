"""Reputation Agent v0 — deterministic, no LLM."""

from __future__ import annotations

import logging
from uuid import UUID

from chromagora_api.services.agent_runs import (
    start_agent_run,
    complete_agent_run,
    fail_agent_run,
)
from chromagora_api.services.context_builder import build_context_packet
from chromagora_api.services.tool_broker import request_tool_execution
from chromagora_schemas.agents import AgentRunCreate
from chromagora_schemas.context import TaskType
from chromagora_schemas.authority import PolicyDecision

logger = logging.getLogger(__name__)


def run_review_request(
    tenant_id: UUID,
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
) -> dict:
    """Execute the Reputation Agent review request workflow.

    1. Start AgentRun
    2. Build ContextPacket
    3. Validate fields
    4. Request reputation.queue_review_request via Tool Broker (dry-run)
    5. Complete AgentRun
    """
    # Step 1: Start AgentRun
    run = start_agent_run(
        tenant_id=tenant_id,
        data=AgentRunCreate(
            business_id=business_id,
            agent_type="reputation",
            trigger_type="manual",
            input_json={
                "customer_name": customer_name,
                "customer_contact": customer_contact,
                "job_summary": job_summary,
                "completed_at": completed_at,
            },
        ),
    )

    if not run:
        return {"status": "failed", "error": "Failed to start agent run"}

    run_id = run.id

    try:
        # Step 2: Build ContextPacket (deterministic)
        import asyncio
        context = asyncio.run(build_context_packet(
            business_id=business_id,
            task_type=TaskType.APPROVAL_CARD_SUMMARY,
            actor_type="agent",
            actor_id=run_id,
            objective="Review request for completed job",
            requested_model_tier=0,
        ))

        # Step 3: Validate fields
        errors = []
        if not customer_name or not customer_name.strip():
            errors.append("customer_name is required")
        if not customer_contact or not customer_contact.strip():
            errors.append("customer_contact is required")
        if not job_summary or not job_summary.strip():
            errors.append("job_summary is required")

        if errors:
            fail_agent_run(run_id, error_message="; ".join(errors))
            return {"status": "failed", "errors": errors}

        # Step 4: Request reputation.queue_review_request via Tool Broker
        tool_result = request_tool_execution(
            business_id=business_id,
            actor_type="agent",
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

        # Step 5: Complete AgentRun
        tool_status = tool_result.get("status", "unknown")
        result = {
            "agent_run_id": str(run_id),
            "tool_name": "reputation.queue_review_request",
            "tool_status": tool_status,
            "context_packet_id": str(context.packet_id),
        }

        complete_agent_run(
            run_id,
            output_json=result,
            model_name="rules-v0",
            model_tier=0,
        )

        return {"status": "completed", **result}

    except Exception as exc:
        logger.exception("Reputation agent failed")
        fail_agent_run(run_id, error_message=str(exc))
        return {"status": "failed", "error": str(exc)}
