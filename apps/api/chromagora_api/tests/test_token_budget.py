"""Tests for TokenBudgetPolicy model tier selection."""

import pytest

from chromagora_api.services.token_budget import select_model_tier
from chromagora_schemas.context import ModelTier, TaskType


class TestDeterministicUpdate:
    def test_always_no_model(self):
        assert select_model_tier(TaskType.DETERMINISTIC_UPDATE) == ModelTier.NO_MODEL

    def test_no_escalation_even_with_high_risk(self):
        # deterministic tasks should never need an LLM
        result = select_model_tier(
            TaskType.DETERMINISTIC_UPDATE,
            risk_level="high",
            dollar_exposure=100000,
        )
        assert result == ModelTier.NO_MODEL


class TestSimpleTasks:
    def test_classification_is_small(self):
        assert select_model_tier(TaskType.SIMPLE_CLASSIFICATION) == ModelTier.SMALL

    def test_extraction_is_small(self):
        assert select_model_tier(TaskType.STRUCTURED_EXTRACTION) == ModelTier.SMALL


class TestCustomerMessageDraft:
    def test_low_risk_is_medium(self):
        assert select_model_tier(
            TaskType.CUSTOMER_MESSAGE_DRAFT,
            risk_level="low",
        ) == ModelTier.MEDIUM

    def test_medium_risk_is_strong(self):
        assert select_model_tier(
            TaskType.CUSTOMER_MESSAGE_DRAFT,
            risk_level="medium",
        ) == ModelTier.STRONG

    def test_high_risk_is_strong(self):
        assert select_model_tier(
            TaskType.CUSTOMER_MESSAGE_DRAFT,
            risk_level="high",
        ) == ModelTier.STRONG


class TestApprovalCardSummary:
    def test_is_medium(self):
        assert select_model_tier(TaskType.APPROVAL_CARD_SUMMARY) == ModelTier.MEDIUM


class TestOpportunityScoring:
    def test_low_dollar_is_medium(self):
        assert select_model_tier(
            TaskType.OPPORTUNITY_SCORING,
            dollar_exposure=1000,
        ) == ModelTier.MEDIUM

    def test_high_dollar_is_strong(self):
        assert select_model_tier(
            TaskType.OPPORTUNITY_SCORING,
            dollar_exposure=10000,
        ) == ModelTier.STRONG


class TestProcurementAnalysis:
    def test_low_dollar_is_medium(self):
        assert select_model_tier(
            TaskType.PROCUREMENT_ANALYSIS,
            dollar_exposure=1000,
        ) == ModelTier.MEDIUM

    def test_high_dollar_is_strong(self):
        assert select_model_tier(
            TaskType.PROCUREMENT_ANALYSIS,
            dollar_exposure=10000,
        ) == ModelTier.STRONG


class TestNegotiationPrep:
    def test_low_dollar_is_strong(self):
        assert select_model_tier(
            TaskType.NEGOTIATION_PREP,
            dollar_exposure=5000,
        ) == ModelTier.STRONG

    def test_very_high_dollar_is_human(self):
        assert select_model_tier(
            TaskType.NEGOTIATION_PREP,
            dollar_exposure=50000,
        ) == ModelTier.HUMAN


class TestComplianceSensitive:
    def test_not_compliant_low_dollar_is_medium(self):
        assert select_model_tier(
            TaskType.COMPLIANCE_SENSITIVE_ACTION,
            compliance_sensitive=False,
            dollar_exposure=100,
        ) == ModelTier.MEDIUM

    def test_compliant_high_dollar_is_human(self):
        assert select_model_tier(
            TaskType.COMPLIANCE_SENSITIVE_ACTION,
            compliance_sensitive=True,
            dollar_exposure=5000,
        ) == ModelTier.HUMAN

    def test_compliant_low_dollar_is_strong(self):
        assert select_model_tier(
            TaskType.COMPLIANCE_SENSITIVE_ACTION,
            compliance_sensitive=True,
            dollar_exposure=100,
        ) == ModelTier.STRONG


class TestBindingCommitment:
    def test_always_human(self):
        assert select_model_tier(TaskType.BINDING_COMMITMENT) == ModelTier.HUMAN

    def test_always_human_even_with_no_dollar(self):
        assert select_model_tier(
            TaskType.BINDING_COMMITMENT,
            dollar_exposure=0,
        ) == ModelTier.HUMAN


class TestEscalation:
    def test_low_confidence_escalates_one_tier(self):
        # SMALL -> MEDIUM
        result = select_model_tier(
            TaskType.SIMPLE_CLASSIFICATION,
            confidence=0.3,
        )
        assert result == ModelTier.MEDIUM

    def test_missing_evidence_escalates_one_tier(self):
        # MEDIUM -> STRONG
        result = select_model_tier(
            TaskType.CUSTOMER_MESSAGE_DRAFT,
            risk_level="low",
            missing_evidence=True,
        )
        assert result == ModelTier.STRONG

    def test_low_confidence_and_missing_evidence_escalates_two_tiers(self):
        # SMALL -> MEDIUM -> STRONG
        result = select_model_tier(
            TaskType.SIMPLE_CLASSIFICATION,
            confidence=0.2,
            missing_evidence=True,
        )
        assert result == ModelTier.STRONG

    def test_escalation_capped_at_human(self):
        result = select_model_tier(
            TaskType.BINDING_COMMITMENT,
            confidence=0.1,
            missing_evidence=True,
        )
        assert result == ModelTier.HUMAN

    def test_high_risk_escalates(self):
        # MEDIUM -> STRONG for customer message
        result = select_model_tier(
            TaskType.CUSTOMER_MESSAGE_DRAFT,
            risk_level="high",
        )
        assert result == ModelTier.STRONG


class TestStringTaskType:
    def test_accepts_string(self):
        result = select_model_tier("deterministic_update")
        assert result == ModelTier.NO_MODEL

    def test_accepts_string_binding(self):
        result = select_model_tier("binding_commitment")
        assert result == ModelTier.HUMAN
