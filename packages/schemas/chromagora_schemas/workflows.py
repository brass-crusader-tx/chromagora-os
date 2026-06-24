"""Workflow-lite engine schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    WAITING_FOR_EXTERNAL_EVENT = "waiting_for_external_event"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str
    version: int = 1
    config_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    pass


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowRunCreate(BaseModel):
    business_id: UUID
    workflow_type: str
    workflow_definition_id: Optional[UUID] = None
    input_json: dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[UUID] = None
    trace_id: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    workflow_definition_id: Optional[UUID] = None
    workflow_type: str
    status: WorkflowStatus
    current_step: Optional[str] = None
    input_json: dict[str, Any] = Field(default_factory=dict)
    state_json: dict[str, Any] = Field(default_factory=dict)
    result_json: Optional[dict[str, Any]] = None
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    correlation_id: Optional[UUID] = None
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkflowStepLogCreate(BaseModel):
    step_name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowStepLogResponse(BaseModel):
    id: UUID
    workflow_run_id: UUID
    step_name: str
    status: WorkflowStepStatus
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
