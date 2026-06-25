"""Agent Registry and Agent Runs API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.base import get_supabase
from chromagora_api.services.agent_registry import (
    create_agent_definition,
    list_agent_definitions,
    create_business_agent_instance,
    list_business_agents,
)
from chromagora_api.services.agent_runs import (
    start_agent_run,
    complete_agent_run,
    fail_agent_run,
    list_agent_runs,
)
from chromagora_schemas.agents import (
    AgentDefinitionCreate,
    BusinessAgentInstanceCreate,
    AgentRunCreate,
)

router = APIRouter(tags=["agents"])


# --- Frontend-facing Agent CRUD ---

@router.get("/agents")
async def list_agents(business_id: UUID | None = None):
    """List agent instances (optionally filtered by business)."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    query = sb.table("business_agent_instances").select("*, agent_definitions(*)")
    if business_id:
        query = query.eq("business_id", str(business_id))
    resp = query.execute()
    return resp.data or []


@router.post("/agents")
async def create_agent(body: AgentDefinitionCreate):
    """Create a new agent definition (simplified — creates definition only)."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    data = body.model_dump()
    resp = sb.table("agent_definitions").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create agent")
    return resp.data[0]


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a single agent instance by ID."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("business_agent_instances")
        .select("*, agent_definitions(*)")
        .eq("id", agent_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    return resp.data[0]


# --- Agent Definitions ---

@router.get("/agents/definitions")
async def get_agent_definitions():
    """List all active agent definitions."""
    return list_agent_definitions()


@router.post("/agents/definitions")
async def post_agent_definition(body: AgentDefinitionCreate):
    """Create a new agent definition."""
    result = create_agent_definition(body)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create agent definition")
    return result


# --- Business Agent Instances ---

@router.get("/businesses/{business_id}/agents")
async def get_business_agents(business_id: UUID):
    """List agent instances for a business."""
    return list_business_agents(business_id)


@router.post("/businesses/{business_id}/agents")
async def post_business_agent(business_id: UUID, body: BusinessAgentInstanceCreate):
    """Create a new business agent instance."""
    # Ensure business_id in path matches body
    body.business_id = business_id
    result = create_business_agent_instance(body)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create agent instance")
    return result


# --- Agent Runs ---

@router.get("/agent-runs")
async def get_agent_runs(business_id: UUID):
    """List agent runs for a business."""
    return list_agent_runs(business_id)
