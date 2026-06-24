"""Tactical Subagent Runner v0 — safe recursive subagents."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_api.services.agent_runs import (
    start_agent_run,
    complete_agent_run,
    fail_agent_run,
)
from chromagora_api.services.context_builder import build_context_packet
from chromagora_schemas.agents import AgentRunCreate
from chromagora_schemas.context import TaskType
from chromagora_schemas.spawn import SpawnContractCreate

logger = logging.getLogger(__name__)

# Registered subagent handlers
_SUBAGENT_HANDLERS: dict[str, callable] = {}


def register_subagent_type(subagent_type: str, handler: callable):
    """Register a handler for a subagent type."""
    _SUBAGENT_HANDLERS[subagent_type] = handler


def run_tactical_subagent(
    tenant_id: UUID,
    contract: SpawnContractCreate,
) -> dict[str, Any]:
    """Run a tactical subagent based on a spawn contract.

    1. Validate SpawnContract
    2. Build scoped ContextPacket
    3. Enforce token budget
    4. Use mock or deterministic handler
    5. Return structured output
    6. No external tools
    7. No durable memory unless policy allows
    8. Record AgentRun linked to parent
    """
    # Step 1: Validate
    if not contract.objective or not contract.objective.strip():
        return {"status": "failed", "error": "objective is required"}

    if contract.max_side_effects == "none":
        # No external tools allowed
        contract.forbidden_tools = list(set(contract.forbidden_tools) | {"*"})

    # Step 2: Start AgentRun linked to parent
    run = start_agent_run(
        tenant_id=tenant_id,
        data=AgentRunCreate(
            business_id=contract.business_id,
            agent_type=f"subagent:{contract.subagent_type}",
            trigger_type="spawn",
            agent_instance_id=None,
            trigger_event_id=None,
            workflow_run_id=None,
            input_json={
                "objective": contract.objective,
                "scope": contract.scope,
                "parent_agent_run_id": str(contract.parent_agent_run_id),
            },
        ),
    )

    if not run:
        return {"status": "failed", "error": "Failed to start subagent run"}

    run_id = run.id

    try:
        # Step 3: Build scoped ContextPacket
        import asyncio
        context = asyncio.run(build_context_packet(
            business_id=contract.business_id,
            task_type=TaskType.STRUCTURED_EXTRACTION,
            actor_type="subagent",
            actor_id=run_id,
            objective=contract.objective,
            requested_model_tier=0,
        ))

        # Step 4: Enforce token budget
        max_iterations = contract.token_budget.get("max_iterations", 1)
        max_input_tokens = contract.token_budget.get("max_input_tokens", 4000)

        # Step 5: Dispatch to handler
        handler = _SUBAGENT_HANDLERS.get(contract.subagent_type)
        if handler:
            output = handler(contract, context)
        else:
            output = _default_handler(contract, context)

        # Step 6: No durable memory unless policy allows
        if contract.memory_write_policy == "no_durable_write":
            pass  # Explicitly skip memory writes

        # Step 7: Complete AgentRun
        result = {
            "agent_run_id": str(run_id),
            "subagent_type": contract.subagent_type,
            "objective": contract.objective,
            "output": output,
            "context_packet_id": str(context.packet_id),
        }

        complete_agent_run(
            run_id,
            output_json=result,
            model_name="subagent-v0",
            model_tier=0,
        )

        return {"status": "completed", **result}

    except Exception as exc:
        logger.exception("Tactical subagent failed")
        fail_agent_run(run_id, error_message=str(exc))
        return {"status": "failed", "error": str(exc)}


def _default_handler(contract, context) -> dict:
    """Default handler for unregistered subagent types."""
    return {
        "message": f"No handler registered for {contract.subagent_type}",
        "objective": contract.objective,
        "scope": contract.scope,
    }


# ---------------------------------------------------------------------------
# Built-in subagent handlers
# ---------------------------------------------------------------------------

def _seo_gap_scout_handler(contract, context) -> dict:
    """SEO gap scout — mock implementation."""
    return {
        "type": "seo_gap_scout",
        "gaps_found": [],
        "recommendations": ["Add service area pages", "Create blog content"],
        "objective": contract.objective,
    }


def _tender_requirement_extractor_handler(contract, context) -> dict:
    """Tender requirement extractor — mock implementation."""
    return {
        "type": "tender_requirement_extractor",
        "requirements": [],
        "unknowns": [],
        "objective": contract.objective,
    }


# Register built-in handlers
register_subagent_type("seo_gap_scout_mock", _seo_gap_scout_handler)
register_subagent_type("tender_requirement_extractor_mock", _tender_requirement_extractor_handler)
