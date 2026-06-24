"""Tests for Tool Broker services."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from chromagora_schemas.tools import (
    ToolDefinitionCreate,
    ToolDefinitionResponse,
    BusinessToolPermissionCreate,
    BusinessToolPermissionResponse,
)


class TestToolDefinitionCreate:
    def test_create(self):
        tool = ToolDefinitionCreate(
            name="crm.create_lead",
            description="Create a lead",
            target_system="crm",
            tool_action="create_lead",
            risk_level="low",
            autonomy_level=3,
        )
        assert tool.name == "crm.create_lead"
        assert tool.is_external_action is False
        assert tool.is_active is True

    def test_external_tool(self):
        tool = ToolDefinitionCreate(
            name="email.send",
            target_system="email",
            tool_action="send",
            is_external_action=True,
            risk_level="high",
        )
        assert tool.is_external_action is True

    def test_default_schema(self):
        tool = ToolDefinitionCreate(
            name="test.tool",
            target_system="test",
            tool_action="run",
        )
        assert tool.input_schema_json == {}
        assert tool.output_schema_json == {}


class TestToolDefinitionResponse:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        resp = ToolDefinitionResponse(
            id=uuid4(),
            name="test.tool",
            target_system="test",
            tool_action="run",
            created_at=now,
            updated_at=now,
        )
        assert resp.id is not None


class TestBusinessToolPermissionCreate:
    def test_create(self):
        perm = BusinessToolPermissionCreate(
            business_id=uuid4(),
            tool_definition_id=uuid4(),
            max_autonomy_level=3,
        )
        assert perm.is_enabled is True
        assert perm.requires_approval_override is None

    def test_approval_override(self):
        perm = BusinessToolPermissionCreate(
            business_id=uuid4(),
            tool_definition_id=uuid4(),
            requires_approval_override=True,
        )
        assert perm.requires_approval_override is True


class TestBusinessToolPermissionResponse:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        resp = BusinessToolPermissionResponse(
            id=uuid4(),
            business_id=uuid4(),
            tool_definition_id=uuid4(),
            created_at=now,
            updated_at=now,
        )
        assert resp.id is not None
