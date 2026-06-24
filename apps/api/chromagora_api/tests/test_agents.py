"""Tests for Agent Registry and Agent Runs."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from chromagora_schemas.agents import (
    AgentDefinitionCreate,
    AgentDefinitionResponse,
    AgentInstanceStatus,
    BusinessAgentInstanceCreate,
    BusinessAgentInstanceResponse,
    AgentRunCreate,
    AgentRunStatus,
)


class TestAgentDefinitionCreate:
    def test_create(self):
        agent = AgentDefinitionCreate(
            name="Sales Agent",
            agent_type="sales",
            description="Handles leads",
            default_authority_level=3,
            default_model_tier=2,
        )
        assert agent.name == "Sales Agent"
        assert agent.default_subscribed_events == []
        assert agent.default_allowed_tools == []
        assert agent.is_active is True

    def test_with_events_and_tools(self):
        agent = AgentDefinitionCreate(
            name="Reputation Agent",
            agent_type="reputation",
            default_subscribed_events=["job.completed"],
            default_allowed_tools=["reputation.queue_review_request"],
        )
        assert len(agent.default_subscribed_events) == 1
        assert len(agent.default_allowed_tools) == 1


class TestAgentDefinitionResponse:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        resp = AgentDefinitionResponse(
            id=uuid4(),
            name="Test Agent",
            agent_type="test",
            created_at=now,
            updated_at=now,
        )
        assert resp.id is not None


class TestBusinessAgentInstanceCreate:
    def test_create(self):
        inst = BusinessAgentInstanceCreate(
            business_id=uuid4(),
            agent_definition_id=uuid4(),
            display_name="My Sales Agent",
        )
        assert inst.status == AgentInstanceStatus.ACTIVE
        assert inst.authority_envelope_id is None

    def test_with_envelope(self):
        inst = BusinessAgentInstanceCreate(
            business_id=uuid4(),
            agent_definition_id=uuid4(),
            display_name="Agent",
            authority_envelope_id=uuid4(),
        )
        assert inst.authority_envelope_id is not None


class TestBusinessAgentInstanceResponse:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        resp = BusinessAgentInstanceResponse(
            id=uuid4(),
            business_id=uuid4(),
            agent_definition_id=uuid4(),
            display_name="Test",
            created_at=now,
            updated_at=now,
        )
        assert resp.id is not None


class TestAgentRunCreate:
    def test_create(self):
        run = AgentRunCreate(
            business_id=uuid4(),
            agent_type="sales",
            trigger_type="manual",
            input_json={"key": "value"},
        )
        assert run.agent_type == "sales"
        assert run.input_json == {"key": "value"}
        assert run.agent_instance_id is None

    def test_with_optional_ids(self):
        run = AgentRunCreate(
            business_id=uuid4(),
            agent_type="reputation",
            trigger_type="event",
            agent_instance_id=uuid4(),
            trigger_event_id=uuid4(),
            workflow_run_id=uuid4(),
        )
        assert run.agent_instance_id is not None
        assert run.trigger_event_id is not None


class TestAgentRunStatus:
    def test_all_statuses(self):
        assert AgentRunStatus.PENDING.value == "pending"
        assert AgentRunStatus.RUNNING.value == "running"
        assert AgentRunStatus.COMPLETED.value == "completed"
        assert AgentRunStatus.FAILED.value == "failed"
        assert AgentRunStatus.CANCELLED.value == "cancelled"


class TestAgentInstanceStatus:
    def test_all_statuses(self):
        assert AgentInstanceStatus.ACTIVE.value == "active"
        assert AgentInstanceStatus.PAUSED.value == "paused"
        assert AgentInstanceStatus.DISABLED.value == "disabled"
