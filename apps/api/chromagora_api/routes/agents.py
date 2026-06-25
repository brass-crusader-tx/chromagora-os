"""Agent Registry and Agent Runs API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import (
    get_active_business_ids,
    get_backend_supabase,
    get_business_tenant_id,
)
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
    try:
        sb = get_backend_supabase()
        active_business_ids = get_active_business_ids(sb)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if business_id:
        if str(business_id) not in active_business_ids:
            raise HTTPException(status_code=404, detail="Business not found")
        active_business_ids = [str(business_id)]
    if not active_business_ids:
        return []
    query = sb.table("business_agent_instances").select("*, agent_definitions(*)")
    query = query.in_("business_id", active_business_ids)
    resp = query.execute()
    # Flatten joined data for frontend
    results = []
    for row in (resp.data or []):
        defs = row.get("agent_definitions") or {}
        results.append({
            "id": row["id"],
            "name": defs.get("name", row.get("display_name", "")),
            "status": row.get("status", "active"),
            "description": defs.get("description"),
            "agent_type": defs.get("agent_type"),
            "created_at": row.get("created_at", ""),
        })
    return results


@router.post("/agents")
async def create_agent(body: AgentDefinitionCreate):
    """Create a new agent definition (simplified — creates definition only)."""
    try:
        sb = get_backend_supabase()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    data = body.model_dump()
    resp = sb.table("agent_definitions").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create agent")
    return resp.data[0]


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a single agent instance by ID."""
    try:
        sb = get_backend_supabase()
        active_business_ids = get_active_business_ids(sb)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not active_business_ids:
        raise HTTPException(status_code=404, detail="Agent not found")
    resp = (
        sb.table("business_agent_instances")
        .select("*, agent_definitions(*)")
        .eq("id", agent_id)
        .in_("business_id", active_business_ids)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    row = resp.data[0]
    defs = row.get("agent_definitions") or {}
    return {
        "id": row["id"],
        "name": defs.get("name", row.get("display_name", "")),
        "status": row.get("status", "active"),
        "description": defs.get("description"),
        "agent_type": defs.get("agent_type"),
        "created_at": row.get("created_at", ""),
    }


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
    try:
        sb = get_backend_supabase()
        if not get_business_tenant_id(str(business_id), sb):
            raise HTTPException(status_code=404, detail="Business not found")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return list_business_agents(business_id)


@router.post("/businesses/{business_id}/agents")
async def post_business_agent(business_id: UUID, body: BusinessAgentInstanceCreate):
    """Create a new business agent instance."""
    try:
        sb = get_backend_supabase()
        if not get_business_tenant_id(str(business_id), sb):
            raise HTTPException(status_code=404, detail="Business not found")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
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
    try:
        sb = get_backend_supabase()
        if not get_business_tenant_id(str(business_id), sb):
            raise HTTPException(status_code=404, detail="Business not found")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return list_agent_runs(business_id)
