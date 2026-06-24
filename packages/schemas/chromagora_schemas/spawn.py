"""Spawn Contract schemas for tactical subagents."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SpawnContractBase(BaseModel):
    parent_agent_run_id: UUID
    business_id: UUID
    subagent_type: str
    objective: str
    scope: Optional[str] = None
    input_refs: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    source_boundaries: dict[str, Any] = Field(default_factory=dict)
    max_side_effects: str = "none"
    ttl_seconds: int = 300
    token_budget: dict[str, Any] = Field(default_factory=dict)
    output_schema_name: Optional[str] = None
    evidence_requirements: list[str] = Field(default_factory=list)
    success_condition: Optional[str] = None
    kill_condition: Optional[str] = None
    authority_level: int = 1
    memory_write_policy: str = "no_durable_write"


class SpawnContractCreate(SpawnContractBase):
    pass


class SpawnContractResponse(SpawnContractBase):
    id: UUID
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
