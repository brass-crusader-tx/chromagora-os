"""Agent Registry — definitions and business agent instances."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_schemas.agents import (
    AgentDefinitionCreate,
    AgentDefinitionResponse,
    BusinessAgentInstanceCreate,
    BusinessAgentInstanceResponse,
)

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db import get_supabase
    return get_supabase()


def _table_admin(name: str):
    from chromagora_api.db import get_supabase_admin
    sb = get_supabase_admin()
    if not sb:
        raise RuntimeError("Database not configured")
    return sb.table(name)


def create_agent_definition(data: AgentDefinitionCreate) -> Optional[AgentDefinitionResponse]:
    """Create a new agent definition."""
    sb = _get_supabase()
    if not sb:
        return None

    payload = {
        "name": data.name,
        "agent_type": data.agent_type,
        "description": data.description,
        "standing_mission": data.standing_mission,
        "default_subscribed_events": data.default_subscribed_events,
        "default_allowed_tools": data.default_allowed_tools,
        "default_authority_level": data.default_authority_level,
        "default_model_tier": data.default_model_tier,
    }
    resp = _table_admin("agent_definitions").insert(payload).execute()
    if not resp.data:
        return None
    return AgentDefinitionResponse(**resp.data[0])


def list_agent_definitions() -> list[dict]:
    """List all active agent definitions."""
    sb = _get_supabase()
    if not sb:
        return []
    resp = (
        sb.table("agent_definitions")
        .select("*")
        .eq("is_active", True)
        .execute()
    )
    return resp.data or []


def create_business_agent_instance(
    data: BusinessAgentInstanceCreate,
) -> Optional[BusinessAgentInstanceResponse]:
    """Create a new business agent instance."""
    sb = _get_supabase()
    if not sb:
        return None

    payload = {
        "business_id": str(data.business_id),
        "agent_definition_id": str(data.agent_definition_id),
        "display_name": data.display_name,
        "status": data.status.value,
        "config_json": data.config_json,
        "authority_envelope_id": str(data.authority_envelope_id) if data.authority_envelope_id else None,
    }
    resp = _table_admin("business_agent_instances").insert(payload).execute()
    if not resp.data:
        return None
    return BusinessAgentInstanceResponse(**resp.data[0])


def list_business_agents(business_id: UUID) -> list[dict]:
    """List agent instances for a business."""
    sb = _get_supabase()
    if not sb:
        return []
    resp = (
        sb.table("business_agent_instances")
        .select("*, agent_definitions(*)")
        .eq("business_id", str(business_id))
        .execute()
    )
    return resp.data or []


def seed_mvp_agents() -> list[str]:
    """Seed MVP agent definitions. Returns list of agent IDs."""
    agents = [
        {
            "name": "Sales Agent",
            "agent_type": "sales",
            "description": "Handles lead management, quote follow-ups, and customer outreach",
            "standing_mission": "Convert leads to customers and ensure timely follow-up on quotes",
            "default_subscribed_events": ["quote.sent", "quote.stale", "lead.created"],
            "default_allowed_tools": ["crm.create_lead", "crm.update_lead_status", "crm.create_followup_task"],
            "default_authority_level": 3,
            "default_model_tier": 2,
        },
        {
            "name": "Reputation Agent",
            "agent_type": "reputation",
            "description": "Manages customer reviews and reputation",
            "standing_mission": "Collect and manage customer reviews to maintain strong reputation",
            "default_subscribed_events": ["job.completed", "review.requested"],
            "default_allowed_tools": ["reputation.queue_review_request"],
            "default_authority_level": 4,
            "default_model_tier": 2,
        },
        {
            "name": "Growth Agent",
            "agent_type": "growth",
            "description": "Identifies growth opportunities and content strategy",
            "standing_mission": "Identify and act on growth opportunities through content and SEO",
            "default_subscribed_events": ["opportunity.detected", "lead.qualified"],
            "default_allowed_tools": ["seo.create_content_draft", "email.create_draft"],
            "default_authority_level": 2,
            "default_model_tier": 2,
        },
        {
            "name": "Procurement Agent",
            "agent_type": "procurement",
            "description": "Manages supplier relationships and procurement opportunities",
            "standing_mission": "Evaluate and act on procurement opportunities within authority",
            "default_subscribed_events": ["opportunity.detected", "procurement_submission"],
            "default_allowed_tools": ["procurement.create_opportunity_note", "supplier.create_supplier_note"],
            "default_authority_level": 2,
            "default_model_tier": 3,
        },
        {
            "name": "Supplier Agent",
            "agent_type": "supplier",
            "description": "Manages supplier notes and evaluations",
            "standing_mission": "Maintain supplier information and evaluations",
            "default_subscribed_events": ["supplier.credit_application"],
            "default_allowed_tools": ["supplier.create_supplier_note"],
            "default_authority_level": 3,
            "default_model_tier": 2,
        },
        {
            "name": "Operations Agent",
            "agent_type": "operations",
            "description": "Coordinates day-to-day operations",
            "standing_mission": "Ensure smooth operational workflow and task completion",
            "default_subscribed_events": ["job.completed", "task.created", "workflow.completed"],
            "default_allowed_tools": ["crm.create_followup_task"],
            "default_authority_level": 3,
            "default_model_tier": 1,
        },
        {
            "name": "Compliance Agent",
            "agent_type": "compliance",
            "description": "Monitors regulatory compliance and policy adherence",
            "standing_mission": "Ensure all actions comply with regulations and internal policies",
            "default_subscribed_events": ["policy.violation_detected", "compliance_sensitive_action"],
            "default_allowed_tools": [],
            "default_authority_level": 1,
            "default_model_tier": 3,
        },
        {
            "name": "Operator Liaison",
            "agent_type": "operator_liaison",
            "description": "Coordinates between automated agents and human operators",
            "standing_mission": "Escalate decisions appropriately and keep operators informed",
            "default_subscribed_events": ["approval.required", "agent.run_failed"],
            "default_allowed_tools": ["message.create_draft"],
            "default_authority_level": 4,
            "default_model_tier": 2,
        },
    ]

    ids = []
    for agent in agents:
        result = create_agent_definition(AgentDefinitionCreate(**agent))
        if result:
            ids.append(str(result.id))

    return ids
