"""Authority Envelope and Policy Kernel schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Autonomy levels
# ---------------------------------------------------------------------------

class AutonomyLevel(int, Enum):
    OBSERVE = 0
    ANALYZE = 1
    DRAFT = 2
    INTERNAL_ACTION = 3
    LOW_RISK_EXTERNAL_ACTION = 4
    BOUNDED_NEGOTIATION = 5
    BINDING_EXECUTION = 6


# ---------------------------------------------------------------------------
# Authority Envelope
# ---------------------------------------------------------------------------

class AuthorityEnvelopeBase(BaseModel):
    business_id: UUID
    name: str
    description: Optional[str] = None
    agent_scope: Optional[str] = None
    tool_scope: Optional[str] = None
    action_type_scope: Optional[str] = None
    autonomy_level: AutonomyLevel = AutonomyLevel.OBSERVE
    max_dollar_exposure: Optional[float] = None
    requires_approval: bool = True
    conditions_json: dict[str, Any] = Field(default_factory=dict)
    forbidden_conditions_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class AuthorityEnvelopeCreate(AuthorityEnvelopeBase):
    pass


class AuthorityEnvelopeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_scope: Optional[str] = None
    tool_scope: Optional[str] = None
    action_type_scope: Optional[str] = None
    autonomy_level: Optional[AutonomyLevel] = None
    max_dollar_exposure: Optional[float] = None
    requires_approval: Optional[bool] = None
    conditions_json: Optional[dict[str, Any]] = None
    forbidden_conditions_json: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class AuthorityEnvelopeResponse(AuthorityEnvelopeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Policy Decision
# ---------------------------------------------------------------------------

class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool = False
    denied: bool = False
    denial_reasons: list[str] = Field(default_factory=list)
    approval_reasons: list[str] = Field(default_factory=list)
    matched_authority_envelope_ids: list[UUID] = Field(default_factory=list)
    max_autonomy_level_allowed: AutonomyLevel = AutonomyLevel.OBSERVE
    model_tier_recommendation: int = 0
    decision_notes: str = ""
    compliance_rule_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Compliance Rule
# ---------------------------------------------------------------------------

class ProposalCreate(BaseModel):
    business_id: UUID
    proposed_by_type: str
    proposed_by_id: UUID
    action_type: str
    title: str
    description: str = ""
    target_system: str = "internal"
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    expected_value: float = 0.0
    confidence: float = 0.5
    risk_level: str = "low"
    autonomy_level_required: int = 0


class ComplianceRuleType(str, Enum):
    CASL_COMMERCIAL_MESSAGE = "casl_commercial_message"
    PRIVACY_PERSONAL_DATA = "privacy_personal_data"
    CALL_RECORDING_NOTICE = "call_recording_notice"
    PUBLIC_CLAIMS = "public_claims"
    REVIEW_REQUEST_POLICY = "review_request_policy"
    PROCUREMENT_SUBMISSION = "procurement_submission"
    SUPPLIER_CREDIT_APPLICATION = "supplier_credit_application"


class ComplianceRuleBase(BaseModel):
    tenant_id: UUID
    business_id: Optional[UUID] = None
    name: str
    jurisdiction: str = "US"
    rule_type: ComplianceRuleType
    description: Optional[str] = None
    applies_to_action_type: Optional[str] = None
    rule_config_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ComplianceRuleCreate(ComplianceRuleBase):
    pass


class ComplianceRuleResponse(ComplianceRuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
