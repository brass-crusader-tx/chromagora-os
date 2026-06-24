"""Agent Registry and Agent Run schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Agent Definition
# ---------------------------------------------------------------------------

class AgentDefinitionBase(BaseModel):
    name: str
    agent_type: str
    description: Optional[str] = None
    standing_mission: Optional[str] = None
    default_subscribed_events: list[str] = Field(default_factory=list)
    default_allowed_tools: list[str] = Field(default_factory=list)
    default_authority_level: int = 1
    default_model_tier: int = 1
    is_active: bool = True


class AgentDefinitionCreate(AgentDefinitionBase):
    pass


class AgentDefinitionResponse(AgentDefinitionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Business Agent Instance
# ---------------------------------------------------------------------------

class AgentInstanceStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class BusinessAgentInstanceBase(BaseModel):
    business_id: UUID
    agent_definition_id: UUID
    display_name: str
    status: AgentInstanceStatus = AgentInstanceStatus.ACTIVE
    config_json: dict[str, Any] = Field(default_factory=dict)
    authority_envelope_id: Optional[UUID] = None


class BusinessAgentInstanceCreate(BusinessAgentInstanceBase):
    pass


class BusinessAgentInstanceResponse(BusinessAgentInstanceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Agent Run
# ---------------------------------------------------------------------------

class AgentRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunCreate(BaseModel):
    business_id: UUID
    agent_type: str
    agent_instance_id: Optional[UUID] = None
    trigger_type: str
    trigger_event_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None
    input_json: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    agent_instance_id: Optional[UUID] = None
    agent_type: str
    trigger_type: str
    trigger_event_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None
    status: AgentRunStatus
    input_json: dict[str, Any] = Field(default_factory=dict)
    context_packet_json: Optional[dict[str, Any]] = None
    output_json: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    cost_estimate: Optional[float] = None
    model_name: Optional[str] = None
    model_tier: Optional[int] = None
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}
