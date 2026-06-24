"""Tool definition and business tool permissions routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional

from chromagora_api.db.base import get_supabase

router = APIRouter(prefix="/businesses/{business_id}/tools", tags=["tools"])


# ---------------------------------------------------------------------------
# Schemas (inline — these are simple CRUD DTOs)
# ---------------------------------------------------------------------------

class ToolPermissionUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    max_autonomy_level: Optional[int] = Field(None, ge=0, le=6)
    requires_approval_override: Optional[bool] = None
    config_json: Optional[dict[str, Any]] = None


class ToolDefinitionResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    target_system: str
    tool_action: str
    risk_level_default: str
    autonomy_level_default: int
    is_external_action: bool
    is_active: bool


class BusinessToolPermissionResponse(BaseModel):
    id: UUID
    business_id: UUID
    tool_definition_id: UUID
    is_enabled: bool
    max_autonomy_level: int
    requires_approval_override: Optional[bool]
    config_json: dict[str, Any]


# ---------------------------------------------------------------------------
# Tool Definitions (global, read-only for businesses)
# ---------------------------------------------------------------------------

@router.get("/definitions", response_model=list[dict])
async def list_tool_definitions(business_id: UUID):
    """List all available tool definitions."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("tool_definitions")
        .select("*")
        .eq("is_active", True)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------------------------
# Business Tool Permissions (per-business enable/disable)
# ---------------------------------------------------------------------------

@router.get("", response_model=list[dict])
async def list_business_tool_permissions(business_id: UUID):
    """List tool permissions for a business, joined with definitions."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")
    resp = (
        sb.table("business_tool_permissions")
        .select("*, tool_definitions(*)")
        .eq("business_id", str(business_id))
        .execute()
    )
    return resp.data or []


@router.post("/{tool_definition_id}/enable", status_code=status.HTTP_201_CREATED)
async def enable_tool(business_id: UUID, tool_definition_id: UUID):
    """Enable a tool for a business."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    # Check tool definition exists
    tool_resp = (
        sb.table("tool_definitions")
        .select("id")
        .eq("id", str(tool_definition_id))
        .execute()
    )
    if not tool_resp.data:
        raise HTTPException(status_code=404, detail="Tool definition not found")

    # Upsert permission
    payload = {
        "business_id": str(business_id),
        "tool_definition_id": str(tool_definition_id),
        "is_enabled": True,
    }
    resp = (
        sb.table("business_tool_permissions")
        .upsert(payload, on_conflict="business_id, tool_definition_id")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to enable tool")
    return resp.data[0]


@router.post("/{tool_definition_id}/disable", status_code=status.HTTP_200_OK)
async def disable_tool(business_id: UUID, tool_definition_id: UUID):
    """Disable a tool for a business."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    resp = (
        sb.table("business_tool_permissions")
        .upsert({
            "business_id": str(business_id),
            "tool_definition_id": str(tool_definition_id),
            "is_enabled": False,
        }, on_conflict="business_id, tool_definition_id")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to disable tool")
    return resp.data[0]


@router.patch("/{tool_definition_id}", status_code=status.HTTP_200_OK)
async def update_tool_permission(
    business_id: UUID,
    tool_definition_id: UUID,
    body: ToolPermissionUpdate,
):
    """Update tool permission settings for a business."""
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503, detail="Database not configured")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = "now()"

    resp = (
        sb.table("business_tool_permissions")
        .upsert(
            {
                "business_id": str(business_id),
                "tool_definition_id": str(tool_definition_id),
                **update_data,
            },
            on_conflict="business_id, tool_definition_id",
        )
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to update tool permission")
    return resp.data[0]
