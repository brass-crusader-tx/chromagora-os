"""Context economy schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Model tiers — ordered from weakest (cheapest) to strongest (most expensive)
# ---------------------------------------------------------------------------

class ModelTier(int, Enum):
    NO_MODEL = 0       # deterministic, no LLM needed
    SMALL = 1          # lightweight model (classification, extraction)
    MEDIUM = 2         # mid-tier (drafts, summaries)
    STRONG = 3         # strong model (analysis, compliance)
    HUMAN = 4          # always human-in-the-loop


# ---------------------------------------------------------------------------
# Task classes — used by TokenBudgetPolicy to select a tier
# ---------------------------------------------------------------------------

class TaskType(str, Enum):
    DETERMINISTIC_UPDATE = "deterministic_update"
    SIMPLE_CLASSIFICATION = "simple_classification"
    STRUCTURED_EXTRACTION = "structured_extraction"
    CUSTOMER_MESSAGE_DRAFT = "customer_message_draft"
    APPROVAL_CARD_SUMMARY = "approval_card_summary"
    OPPORTUNITY_SCORING = "opportunity_scoring"
    PROCUREMENT_ANALYSIS = "procurement_analysis"
    NEGOTIATION_PREP = "negotiation_prep"
    COMPLIANCE_SENSITIVE_ACTION = "compliance_sensitive_action"
    BINDING_COMMITMENT = "binding_commitment"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceItem(BaseModel):
    source_type: str            # e.g. "event", "action", "claim", "manual"
    source_id: Optional[UUID] = None
    title: str
    snippet: str = ""
    url: Optional[str] = None
    timestamp: Optional[datetime] = None
    confidence: float = 1.0


class EvidenceBundle(BaseModel):
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    source_summary: str = ""


# ---------------------------------------------------------------------------
# Context budget
# ---------------------------------------------------------------------------

class ContextBudget(BaseModel):
    max_input_tokens: int = 8000
    max_output_tokens: int = 2000
    max_iterations: int = 1
    allow_retrieval: bool = False
    allow_full_artifacts: bool = False
    allow_subagents: bool = False
    escalation_model_tier: ModelTier = ModelTier.MEDIUM


# ---------------------------------------------------------------------------
# Context packet — the core unit of work passed to an LLM or agent
# ---------------------------------------------------------------------------

class ContextPacket(BaseModel):
    packet_id: UUID
    tenant_id: UUID
    business_id: Optional[UUID] = None
    task_type: TaskType
    actor_type: str            # "user", "agent", "system", "workflow"
    actor_id: Optional[UUID] = None
    model_tier: ModelTier
    context_budget: ContextBudget
    objective: str
    authority_summary: str = ""
    business_twin_slice: dict[str, Any] = Field(default_factory=dict)
    workflow_state: dict[str, Any] = Field(default_factory=dict)
    relevant_events: list[dict[str, Any]] = Field(default_factory=list)
    evidence_bundle: EvidenceBundle = Field(default_factory=EvidenceBundle)
    retrieved_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    forbidden_claims: list[dict[str, Any]] = Field(default_factory=list)
    approved_claims: list[dict[str, Any]] = Field(default_factory=list)
    output_schema_name: Optional[str] = None
    escalation_conditions: dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
