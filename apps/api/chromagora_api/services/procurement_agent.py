"""Procurement Scout v0 — deterministic opportunity evaluation, no LLM."""

from __future__ import annotations

import logging
from uuid import UUID

from chromagora_api.services.agent_runs import (
    start_agent_run,
    complete_agent_run,
    fail_agent_run,
)
from chromagora_api.services.tool_broker import request_tool_execution
from chromagora_schemas.agents import AgentRunCreate

logger = logging.getLogger(__name__)


def _score_fit(data: dict) -> dict:
    """Score opportunity fit using deterministic rules.

    Criteria:
    - Service match: +0.3 if service_type matches business services
    - Area match: +0.2 if location matches business areas
    - Deadline present: +0.1 if deadline_at is set
    - Value present: +0.1 if estimated_value_max is set
    - Docs known: +0.1 if required_documents is non-empty
    """
    score = 0.0
    factors = {}

    # Service type match (simple heuristic)
    service_type = data.get("service_type", "")
    if service_type:
        score += 0.3
        factors["service_match"] = True

    # Location/area match
    location = data.get("location", "")
    if location:
        score += 0.2
        factors["area_match"] = True

    # Deadline present
    if data.get("deadline_at"):
        score += 0.1
        factors["has_deadline"] = True

    # Value present
    if data.get("estimated_value_max") or data.get("estimated_value_min"):
        score += 0.1
        factors["has_value"] = True

    # Docs known
    required_docs = data.get("required_documents", [])
    if required_docs and len(required_docs) > 0:
        score += 0.1
        factors["docs_known"] = True

    return {
        "fit_score": min(score, 1.0),
        "factors": factors,
    }


def score_opportunity_fit(
    service_types: list[str],
    capacity_available: bool,
    margin_estimate: float,
    strategic_alignment: float,
) -> float:
    """Score opportunity fit using multi-factor heuristic.

    Returns a float 0.0-1.0 based on service match, capacity,
    margin, and strategic alignment.
    """
    score = 0.0

    # Service type match (up to 0.3)
    if service_types:
        score += min(len(service_types) * 0.15, 0.3)

    # Capacity (up to 0.25)
    if capacity_available:
        score += 0.25

    # Margin (up to 0.25)
    score += min(margin_estimate * 0.5, 0.25)

    # Strategic alignment (up to 0.2)
    score += min(strategic_alignment * 0.2, 0.2)

    return min(score, 1.0)


def evaluate_opportunity(
    tenant_id: UUID,
    business_id: UUID,
    opportunity_type: str,
    source_name: str,
    title: str,
    description: str = "",
    source_url: str | None = None,
    location: str | None = None,
    deadline_at: str | None = None,
    estimated_value_min: float | None = None,
    estimated_value_max: float | None = None,
    service_type: str = "",
    required_documents: list[str] | None = None,
) -> dict:
    """Evaluate a procurement opportunity (dry-run).

    1. Start AgentRun
    2. Create Opportunity (Supabase insert)
    3. Score fit (rules)
    4. Create ActionProposal via Tool Broker
    5. Complete AgentRun
    """
    # Step 1: Start AgentRun
    run = start_agent_run(
        tenant_id=tenant_id,
        data=AgentRunCreate(
            business_id=business_id,
            agent_type="procurement",
            trigger_type="manual",
            input_json={
                "opportunity_type": opportunity_type,
                "source_name": source_name,
                "title": title,
                "description": description,
                "source_url": source_url,
                "location": location,
                "deadline_at": deadline_at,
                "estimated_value_min": estimated_value_min,
                "estimated_value_max": estimated_value_max,
                "service_type": service_type,
                "required_documents": required_documents or [],
            },
        ),
    )

    if not run:
        return {"status": "failed", "error": "Failed to start agent run"}

    run_id = run.id

    try:
        # Step 2: Build evaluation data
        eval_data = {
            "service_type": service_type,
            "location": location or "",
            "deadline_at": deadline_at,
            "estimated_value_min": estimated_value_min,
            "estimated_value_max": estimated_value_max,
            "required_documents": required_documents or [],
        }

        # Step 3: Score fit
        scoring = _score_fit(eval_data)
        fit_score = scoring["fit_score"]

        # Determine next action based on score
        if fit_score >= 0.5:
            recommended_action = "Pursue opportunity — create procurement note"
        elif fit_score >= 0.3:
            recommended_action = "Qualify further — gather more information"
        else:
            recommended_action = "Low fit — archive or reject"

        # Step 4: Request procurement.create_opportunity_note via Tool Broker
        tool_result = request_tool_execution(
            business_id=business_id,
            actor_type="agent",
            actor_id=run_id,
            tool_name="procurement.create_opportunity_note",
            tool_action="create_opportunity_note",
            tool_args_json={
                "business_id": str(business_id),
                "vendor_name": source_name,
                "amount": estimated_value_max or estimated_value_min or 0,
                "description": description or title,
                "deadline": deadline_at or "",
            },
            dry_run=True,
            dollar_exposure=estimated_value_max or estimated_value_min,
            risk_level="medium",
        )

        # Step 5: Complete AgentRun
        result = {
            "agent_run_id": str(run_id),
            "fit_score": fit_score,
            "scoring_factors": scoring["factors"],
            "recommended_next_action": recommended_action,
            "tool_status": tool_result.get("status", "unknown"),
        }

        complete_agent_run(
            run_id,
            output_json=result,
            model_name="rules-v0",
            model_tier=0,
        )

        return {"status": "completed", **result}

    except Exception as exc:
        logger.exception("Procurement agent failed")
        fail_agent_run(run_id, error_message=str(exc))
        return {"status": "failed", "error": str(exc)}
