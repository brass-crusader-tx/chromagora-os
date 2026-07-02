"""Event and ledger schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    BUSINESS_CREATED = "business.created"
    BUS_TWIN_UPDATED = "business_twin.updated"
    LEAD_CREATED = "lead.created"
    LEAD_QUALIFIED = "lead.qualified"
    QUOTE_SENT = "quote.sent"
    QUOTE_STALE = "quote.stale"
    QUOTE_FOLLOW_UP_PROPOSED = "quote.follow_up_proposed"
    QUOTE_FOLLOW_UP_APPROVED = "quote.follow_up_approved"
    QUOTE_FOLLOW_UP_REJECTED = "quote.follow_up_rejected"
    QUOTE_FOLLOW_UP_EXECUTED = "quote.follow_up_executed"
    QUOTE_FOLLOW_UP_FAILED = "quote.follow_up_failed"
    QUOTE_STATUS_CHANGED = "quote.status_changed"
    JOB_COMPLETED = "job.completed"
    REVIEW_REQUESTED = "review.requested"
    REVIEW_RECEIVED = "review.received"
    OPPORTUNITY_DETECTED = "opportunity.detected"
    APPROVAL_REQUIRED = "approval.required"
    ACTION_PROPOSED = "action.proposed"
    ACTION_APPROVED = "action.approved"
    ACTION_REJECTED = "action.rejected"
    ACTION_EXECUTED = "action.executed"
    ACTION_FAILED = "action.failed"
    POLICY_VIOLATION_DETECTED = "policy.violation_detected"
    AGENT_RUN_STARTED = "agent.run_started"
    AGENT_RUN_COMPLETED = "agent.run_completed"
    AGENT_RUN_FAILED = "agent.run_failed"


class EventBase(BaseModel):
    event_type: EventType
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    payload_json: dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None


class EventResponse(EventBase):
    id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    occurred_at: datetime
    created_at: datetime
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class ActionProposalBase(BaseModel):
    action_type: str
    title: str
    description: Optional[str] = None
    target_system: Optional[str] = None
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "low"
    autonomy_level_required: int = 0


class ActionProposalCreate(ActionProposalBase):
    pass


class ActionProposalResponse(ActionProposalBase):
    id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    proposed_by_type: str
    proposed_by_id: Optional[UUID] = None
    status: str
    expected_value: Optional[float] = None
    confidence: Optional[float] = None
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    policy_decision_json: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ApprovalResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    action_proposal_id: UUID
    status: str
    requested_by_type: str
    requested_by_id: Optional[UUID] = None
    requested_at: datetime
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}


class LedgerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    action_proposal_id: Optional[UUID] = None
    approval_request_id: Optional[UUID] = None
    tool_name: str
    tool_action: str
    result_status: str
    result_json: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    executed_by_type: str
    executed_by_id: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    reversibility: str
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}
