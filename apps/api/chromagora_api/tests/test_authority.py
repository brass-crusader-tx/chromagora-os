"""Tests for Authority Envelope schemas and routes."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from chromagora_schemas.authority import (
    AuthorityEnvelopeBase,
    AuthorityEnvelopeCreate,
    AuthorityEnvelopeResponse,
    AuthorityEnvelopeUpdate,
    AutonomyLevel,
)


class TestAutonomyLevel:
    def test_ordering(self):
        assert AutonomyLevel.OBSERVE.value < AutonomyLevel.ANALYZE.value
        assert AutonomyLevel.ANALYZE.value < AutonomyLevel.DRAFT.value
        assert AutonomyLevel.DRAFT.value < AutonomyLevel.INTERNAL_ACTION.value
        assert AutonomyLevel.INTERNAL_ACTION.value < AutonomyLevel.LOW_RISK_EXTERNAL_ACTION.value
        assert AutonomyLevel.LOW_RISK_EXTERNAL_ACTION.value < AutonomyLevel.BOUNDED_NEGOTIATION.value
        assert AutonomyLevel.BOUNDED_NEGOTIATION.value < AutonomyLevel.BINDING_EXECUTION.value

    def test_from_int(self):
        assert AutonomyLevel(0) == AutonomyLevel.OBSERVE
        assert AutonomyLevel(6) == AutonomyLevel.BINDING_EXECUTION


class TestAuthorityEnvelopeCreate:
    def test_create(self):
        env = AuthorityEnvelopeCreate(
            business_id=uuid4(),
            name="Sales Agent",
            autonomy_level=AutonomyLevel.DRAFT,
            max_dollar_exposure=500.0,
            requires_approval=True,
        )
        assert env.name == "Sales Agent"
        assert env.autonomy_level == AutonomyLevel.DRAFT
        assert env.max_dollar_exposure == 500.0
        assert env.is_active is True

    def test_default_autonomy_is_observe(self):
        env = AuthorityEnvelopeCreate(
            business_id=uuid4(),
            name="Observer",
        )
        assert env.autonomy_level == AutonomyLevel.OBSERVE

    def test_null_scope_is_none(self):
        env = AuthorityEnvelopeCreate(
            business_id=uuid4(),
            name="Full Access",
        )
        assert env.agent_scope is None
        assert env.tool_scope is None
        assert env.action_type_scope is None


class TestAuthorityEnvelopeUpdate:
    def test_partial_update(self):
        update = AuthorityEnvelopeUpdate(
            name="Updated Name",
            autonomy_level=AutonomyLevel.INTERNAL_ACTION,
        )
        assert update.name == "Updated Name"
        assert update.autonomy_level == AutonomyLevel.INTERNAL_ACTION
        assert update.max_dollar_exposure is None

    def test_model_dump_exclude_unset(self):
        update = AuthorityEnvelopeUpdate(name="Only Name")
        dumped = update.model_dump(exclude_unset=True)
        assert "name" in dumped
        assert "autonomy_level" not in dumped


class TestAuthorityEnvelopeResponse:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        resp = AuthorityEnvelopeResponse(
            id=uuid4(),
            business_id=uuid4(),
            name="Test",
            autonomy_level=AutonomyLevel.ANALYZE,
            created_at=now,
            updated_at=now,
        )
        assert resp.id is not None
        assert resp.autonomy_level == AutonomyLevel.ANALYZE
