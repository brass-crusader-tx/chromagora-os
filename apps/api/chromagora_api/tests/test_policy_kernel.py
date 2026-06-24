"""Tests for Policy Kernel evaluator."""

import pytest
from unittest.mock import patch
from uuid import uuid4

from chromagora_api.services.policy_kernel import evaluate_action_policy
from chromagora_schemas.authority import AutonomyLevel, PolicyDecision


def _make_envelope(
    id=None,
    autonomy_level=3,
    max_dollar_exposure=None,
    agent_scope=None,
    action_type_scope=None,
    forbidden_conditions_json=None,
    is_active=True,
):
    return {
        "id": str(id or uuid4()),
        "business_id": str(uuid4()),
        "autonomy_level": autonomy_level,
        "max_dollar_exposure": max_dollar_exposure,
        "agent_scope": agent_scope,
        "action_type_scope": action_type_scope,
        "forbidden_conditions_json": forbidden_conditions_json or {},
        "is_active": is_active,
    }


class TestNoMatchingEnvelope:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_no_envelopes_requires_approval(self, mock_load):
        mock_load.return_value = []
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="customer_message_draft",
            target_system="sms",
            autonomy_level_requested=2,
        )
        assert result.requires_approval is True
        assert "No matching authority envelope" in result.approval_reasons[0]


class TestAutonomyExceeds:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_autonomy_exceeds_requires_approval(self, mock_load):
        mock_load.return_value = [_make_envelope(autonomy_level=2)]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="internal_action",
            target_system="crm",
            autonomy_level_requested=4,
        )
        assert result.requires_approval is True
        assert any("autonomy level" in r for r in result.approval_reasons)

    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_autonomy_within_limit_allowed(self, mock_load):
        mock_load.return_value = [_make_envelope(autonomy_level=4)]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="internal_action",
            target_system="crm",
            autonomy_level_requested=3,
        )
        assert result.allowed is True


class TestDollarExposure:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_dollar_exceeds_requires_approval(self, mock_load):
        mock_load.return_value = [_make_envelope(
            autonomy_level=4,
            max_dollar_exposure=1000.0,
        )]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="internal_action",
            target_system="crm",
            autonomy_level_requested=3,
            dollar_exposure=5000.0,
        )
        assert result.requires_approval is True
        assert any("Dollar exposure" in r for r in result.approval_reasons)

    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_dollar_within_limit(self, mock_load):
        mock_load.return_value = [_make_envelope(
            autonomy_level=4,
            max_dollar_exposure=5000.0,
        )]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="internal_action",
            target_system="crm",
            autonomy_level_requested=3,
            dollar_exposure=1000.0,
        )
        assert result.allowed is True


class TestLevel6AlwaysRequiresApproval:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_level_6_always_requires_approval(self, mock_load):
        mock_load.return_value = [_make_envelope(autonomy_level=6)]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="binding_execution",
            target_system="crm",
            autonomy_level_requested=6,
        )
        assert result.requires_approval is True
        assert any("level 6" in r.lower() or "binding" in r.lower() for r in result.approval_reasons)


class TestForbiddenConditions:
    @patch("chromagora_api.services.policy_kernel._load_active_compliance_rules", return_value=[])
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_forbidden_condition_denies(self, mock_load, mock_compliance):
        mock_load.return_value = [_make_envelope(
            autonomy_level=4,
            forbidden_conditions_json={"channel": "unsolicited_sms"},
        )]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="customer_message_draft",
            target_system="sms",
            autonomy_level_requested=2,
            payload_json={"channel": "unsolicited_sms"},
        )
        assert result.denied is True
        assert len(result.denial_reasons) > 0
        assert "Forbidden" in result.denial_reasons[0]

    @patch("chromagora_api.services.policy_kernel._load_active_compliance_rules", return_value=[])
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_no_forbidden_condition_allows(self, mock_load, mock_compliance):
        mock_load.return_value = [_make_envelope(
            autonomy_level=4,
            forbidden_conditions_json={"channel": "unsolicited_sms"},
        )]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="customer_message_draft",
            target_system="sms",
            autonomy_level_requested=2,
            payload_json={"channel": "email"},
        )
        assert result.denied is not True


class TestComplianceSensitive:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_compliance_sensitive_requires_approval(self, mock_load):
        mock_load.return_value = [_make_envelope(autonomy_level=4)]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="compliance_sensitive_action",
            target_system="crm",
            autonomy_level_requested=2,
            compliance_sensitive=True,
        )
        assert result.requires_approval is True
        assert any("compliance-sensitive" in r for r in result.approval_reasons)


class TestWildcardScopes:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_null_agent_scope_matches_any(self, mock_load):
        mock_load.return_value = [_make_envelope(
            autonomy_level=3,
            agent_scope=None,
            action_type_scope=None,
        )]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="any_agent_type",
            actor_id=uuid4(),
            action_type="some_action",
            target_system="crm",
            autonomy_level_requested=2,
        )
        assert len(result.matched_authority_envelope_ids) == 1

    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_restricted_agent_scope_filters(self, mock_load):
        mock_load.return_value = [_make_envelope(
            autonomy_level=3,
            agent_scope="sales_agent",
        )]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="field_agent",
            actor_id=uuid4(),
            action_type="some_action",
            target_system="crm",
            autonomy_level_requested=2,
        )
        assert len(result.matched_authority_envelope_ids) == 0


class TestModelTierRecommendation:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_model_tier_is_recommended(self, mock_load):
        mock_load.return_value = [_make_envelope(autonomy_level=4)]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="procurement_analysis",
            target_system="crm",
            autonomy_level_requested=2,
            dollar_exposure=10000.0,
        )
        assert result.model_tier_recommendation >= 0
        assert result.model_tier_recommendation == 3


class TestMaxAutonomyAllowed:
    @patch("chromagora_api.services.policy_kernel._load_active_envelopes")
    def test_max_autonomy_from_envelopes(self, mock_load):
        mock_load.return_value = [
            _make_envelope(autonomy_level=2),
            _make_envelope(autonomy_level=4),
        ]
        result = evaluate_action_policy(
            business_id=uuid4(),
            actor_type="agent",
            actor_id=uuid4(),
            action_type="internal_action",
            target_system="crm",
            autonomy_level_requested=1,
        )
        assert result.max_autonomy_level_allowed == AutonomyLevel.LOW_RISK_EXTERNAL_ACTION
