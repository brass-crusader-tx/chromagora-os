"""Sales Agent v0 — deterministic, no LLM."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
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

logger = logging.getLogger(__name__)

STALE_QUOTE_DAYS = 3


def run_stale_quote_followup(
    tenant_id: UUID,
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    service_type: str,
    quote_sent_at: str,
    quote_id: str | None = None,
    quote_amount: float | None = None,
    last_contact_at: str | None = None,
) -> dict:
    """Execute the Sales Agent stale quote follow-up workflow.

    1. Start AgentRun
    2. Build ContextPacket
    3. Determine stale
    4. If stale -> request crm.create_followup_task via Tool Broker
    5. Complete AgentRun
    """
    # Step 1: Start AgentRun
    run = start_agent_run(
        tenant_id=tenant_id,
        data=AgentRunCreate(
            business_id=business_id,
            agent_type="sales",
            trigger_type="manual",
            input_json={
                "customer_name": customer_name,
                "customer_contact": customer_contact,
                "service_type": service_type,
                "quote_sent_at": quote_sent_at,
                "quote_id": quote_id,
                "quote_amount": quote_amount,
                "last_contact_at": last_contact_at,
            },
        ),
    )

    if not run:
        return {"status": "failed", "error": "Failed to start agent run"}

    run_id = run.id

    try:
        # Step 2: Build ContextPacket
        import asyncio
        context = asyncio.run(build_context_packet(
            business_id=business_id,
            task_type=TaskType.SIMPLE_CLASSIFICATION,
            actor_type="agent",
            actor_id=run_id,
            objective="Stale quote follow-up",
            requested_model_tier=0,
        ))

        # Step 3: Validate
        errors = []
        if not customer_name or not customer_name.strip():
            errors.append("customer_name is required")
        if not customer_contact or not customer_contact.strip():
            errors.append("customer_contact is required")
        if not service_type or not service_type.strip():
            errors.append("service_type is required")
        if not quote_sent_at:
            errors.append("quote_sent_at is required")

        if errors:
            fail_agent_run(run_id, error_message="; ".join(errors))
            return {"status": "failed", "errors": errors}

        # Step 4: Determine stale
        try:
            sent_at = datetime.fromisoformat(quote_sent_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            sent_at = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS + 1)

        stale_threshold = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS)
        is_stale = sent_at < stale_threshold

        if not is_stale:
            complete_agent_run(
                run_id,
                output_json={
                    "action": "none",
                    "reason": "Quote is not stale",
                },
                model_name="rules-v0",
                model_tier=0,
            )
            return {"status": "completed", "action": "none", "reason": "not_stale"}

        # Step 5: If stale -> request crm.create_followup_task
        tool_result = request_tool_execution(
            business_id=business_id,
            actor_type="agent",
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

        # Step 6: Complete AgentRun
        tool_status = tool_result.get("status", "unknown")
        result = {
            "agent_run_id": str(run_id),
            "tool_name": "crm.create_followup_task",
            "tool_status": tool_status,
            "is_stale": True,
            "context_packet_id": str(context.packet_id),
        }

        complete_agent_run(
            run_id,
            output_json=result,
            model_name="rules-v0",
            model_tier=0,
        )

        return {"status": "completed", "action": "follow_up_task_created", **result}

    except Exception as exc:
        logger.exception("Sales agent failed")
        fail_agent_run(run_id, error_message=str(exc))
        return {"status": "failed", "error": str(exc)}
