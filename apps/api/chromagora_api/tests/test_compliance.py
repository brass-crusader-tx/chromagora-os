"""Tests for Compliance Rule schemas."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from chromagora_schemas.authority import (
    ComplianceRuleBase,
    ComplianceRuleCreate,
    ComplianceRuleResponse,
    ComplianceRuleType,
)


class TestComplianceRuleType:
    def test_all_types(self):
        assert ComplianceRuleType.CASL_COMMERCIAL_MESSAGE.value == "casl_commercial_message"
        assert ComplianceRuleType.PRIVACY_PERSONAL_DATA.value == "privacy_personal_data"
        assert ComplianceRuleType.CALL_RECORDING_NOTICE.value == "call_recording_notice"
        assert ComplianceRuleType.PUBLIC_CLAIMS.value == "public_claims"
        assert ComplianceRuleType.REVIEW_REQUEST_POLICY.value == "review_request_policy"
        assert ComplianceRuleType.PROCUREMENT_SUBMISSION.value == "procurement_submission"
        assert ComplianceRuleType.SUPPLIER_CREDIT_APPLICATION.value == "supplier_credit_application"


class TestComplianceRuleCreate:
    def test_create(self):
        rule = ComplianceRuleCreate(
            tenant_id=uuid4(),
            name="CASL Commercial Message Rule",
            rule_type=ComplianceRuleType.CASL_COMMERCIAL_MESSAGE,
            jurisdiction="CA",
            description="Requires consent for commercial SMS",
            applies_to_action_type="customer_message_draft",
            rule_config_json={"blocking": True, "require_consent": True},
        )
        assert rule.name == "CASL Commercial Message Rule"
        assert rule.jurisdiction == "CA"
        assert rule.rule_config_json["blocking"] is True

    def test_default_jurisdiction(self):
        rule = ComplianceRuleCreate(
            tenant_id=uuid4(),
            name="US Rule",
            rule_type=ComplianceRuleType.PUBLIC_CLAIMS,
        )
        assert rule.jurisdiction == "US"
        assert rule.business_id is None
        assert rule.applies_to_action_type is None

    def test_tenant_wide_rule(self):
        rule = ComplianceRuleCreate(
            tenant_id=uuid4(),
            name="Tenant-wide privacy",
            rule_type=ComplianceRuleType.PRIVACY_PERSONAL_DATA,
        )
        assert rule.business_id is None  # tenant-wide

    def test_business_specific_rule(self):
        rule = ComplianceRuleCreate(
            tenant_id=uuid4(),
            business_id=uuid4(),
            name="Business-specific rule",
            rule_type=ComplianceRuleType.PROCUREMENT_SUBMISSION,
        )
        assert rule.business_id is not None


class TestComplianceRuleResponse:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        resp = ComplianceRuleResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Test Rule",
            rule_type=ComplianceRuleType.REVIEW_REQUEST_POLICY,
            created_at=now,
            updated_at=now,
        )
        assert resp.id is not None
        assert resp.is_active is True
