"""Opportunity schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityStatus(str, Enum):
    DETECTED = "detected"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    APPROVAL_REQUIRED = "approval_required"
    PURSUING = "pursuing"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"


class OpportunityBase(BaseModel):
    business_id: UUID
    opportunity_type: str
    source_name: str
    source_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    published_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    estimated_value_min: Optional[float] = None
    estimated_value_max: Optional[float] = None
    fit_score: Optional[float] = None
    urgency_score: Optional[float] = None
    capacity_fit: Optional[float] = None
    margin_confidence: Optional[float] = None
    strategic_value: Optional[float] = None
    status: OpportunityStatus = OpportunityStatus.DETECTED
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    recommended_next_action: Optional[str] = None
    agent_owner: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityResponse(OpportunityBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}
