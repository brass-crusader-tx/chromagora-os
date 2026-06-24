"""Tests for context packet schemas."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from chromagora_schemas.context import (
    ContextBudget,
    ContextPacket,
    EvidenceBundle,
    EvidenceItem,
    ModelTier,
    TaskType,
)


class TestEvidenceItem:
    def test_create(self):
        item = EvidenceItem(
            source_type="event",
            source_id=uuid4(),
            title="Test event",
            snippet="A snippet",
            confidence=0.9,
        )
        assert item.source_type == "event"
        assert item.confidence == 0.9

    def test_defaults(self):
        item = EvidenceItem(source_type="manual", title="Manual note")
        assert item.confidence == 1.0
        assert item.snippet == ""
        assert item.source_id is None


class TestEvidenceBundle:
    def test_empty(self):
        bundle = EvidenceBundle()
        assert bundle.evidence_items == []
        assert bundle.missing_evidence == []
        assert bundle.confidence == 1.0

    def test_with_items(self):
        items = [
            EvidenceItem(source_type="event", title="E1", confidence=0.8),
            EvidenceItem(source_type="event", title="E2", confidence=0.6),
        ]
        bundle = EvidenceBundle(
            evidence_items=items,
            missing_evidence=["photo_id"],
            confidence=0.7,
        )
        assert len(bundle.evidence_items) == 2
        assert bundle.missing_evidence == ["photo_id"]


class TestContextBudget:
    def test_defaults(self):
        budget = ContextBudget()
        assert budget.max_input_tokens == 8000
        assert budget.max_output_tokens == 2000
        assert budget.max_iterations == 1
        assert budget.allow_retrieval is False
        assert budget.allow_full_artifacts is False
        assert budget.allow_subagents is False
        assert budget.escalation_model_tier == ModelTier.MEDIUM

    def test_custom(self):
        budget = ContextBudget(
            max_input_tokens=16000,
            max_output_tokens=4000,
            allow_retrieval=True,
            escalation_model_tier=ModelTier.STRONG,
        )
        assert budget.max_input_tokens == 16000
        assert budget.allow_retrieval is True
        assert budget.escalation_model_tier == ModelTier.STRONG


class TestContextPacket:
    def test_create(self):
        packet = ContextPacket(
            packet_id=uuid4(),
            tenant_id=uuid4(),
            business_id=uuid4(),
            task_type=TaskType.CUSTOMER_MESSAGE_DRAFT,
            actor_type="user",
            actor_id=uuid4(),
            model_tier=ModelTier.MEDIUM,
            context_budget=ContextBudget(),
            objective="Draft a quote follow-up email",
            created_at=datetime.now(timezone.utc),
        )
        assert packet.task_type == TaskType.CUSTOMER_MESSAGE_DRAFT
        assert packet.model_tier == ModelTier.MEDIUM
        assert packet.actor_type == "user"

    def test_from_attributes(self):
        """Test that the model can be constructed from ORM-style attributes."""
        now = datetime.now(timezone.utc)
        packet = ContextPacket(
            packet_id=uuid4(),
            tenant_id=uuid4(),
            task_type=TaskType.DETERMINISTIC_UPDATE,
            actor_type="system",
            model_tier=ModelTier.NO_MODEL,
            context_budget=ContextBudget(),
            objective="Update capacity score",
            created_at=now,
        )
        assert packet.model_tier.value == 0
        assert packet.business_id is None

    def test_nested_evidence(self):
        bundle = EvidenceBundle(
            evidence_items=[
                EvidenceItem(source_type="event", title="E1"),
            ],
        )
        packet = ContextPacket(
            packet_id=uuid4(),
            tenant_id=uuid4(),
            task_type=TaskType.APPROVAL_CARD_SUMMARY,
            actor_type="agent",
            model_tier=ModelTier.MEDIUM,
            context_budget=ContextBudget(),
            objective="Summarize approval card",
            evidence_bundle=bundle,
            created_at=datetime.now(timezone.utc),
        )
        assert len(packet.evidence_bundle.evidence_items) == 1


class TestModelTier:
    def test_ordering(self):
        assert ModelTier.NO_MODEL.value < ModelTier.SMALL.value
        assert ModelTier.SMALL.value < ModelTier.MEDIUM.value
        assert ModelTier.MEDIUM.value < ModelTier.STRONG.value
        assert ModelTier.STRONG.value < ModelTier.HUMAN.value

    def test_from_int(self):
        assert ModelTier(0) == ModelTier.NO_MODEL
        assert ModelTier(4) == ModelTier.HUMAN


class TestTaskType:
    def test_values(self):
        assert TaskType.DETERMINISTIC_UPDATE.value == "deterministic_update"
        assert TaskType.BINDING_COMMITMENT.value == "binding_commitment"
