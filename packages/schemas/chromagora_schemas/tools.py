"""Tool Broker schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ToolDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_system: str
    tool_action: str
    input_schema_json: dict[str, Any] = Field(default_factory=dict)
    output_schema_json: dict[str, Any] = Field(default_factory=dict)
    risk_level_default: str = "low"
    autonomy_level_required_default: int = 1
    is_external_action: bool = False
    is_active: bool = True


class ToolDefinitionCreate(ToolDefinitionBase):
    pass


class ToolDefinitionResponse(ToolDefinitionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessToolPermissionBase(BaseModel):
    business_id: UUID
    tool_definition_id: UUID
    is_enabled: bool = True
    max_autonomy_level: int = 1
    requires_approval_override: Optional[bool] = None
    config_json: dict[str, Any] = Field(default_factory=dict)


class BusinessToolPermissionCreate(BusinessToolPermissionBase):
    pass


class BusinessToolPermissionResponse(BusinessToolPermissionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
