"""TokenBudgetPolicy service — model tier selection based on task characteristics."""

from __future__ import annotations

import logging
from typing import Optional

from chromagora_schemas.context import ModelTier, TaskType

logger = logging.getLogger(__name__)

# Dollar thresholds for tier escalation
PROCUREMENT_DOLLAR_THRESHOLD = 5000    # above this -> STRONG
NEGOTIATION_DOLLAR_THRESHOLD = 10000   # above this -> HUMAN
COMPLIANCE_DOLLAR_THRESHOLD = 1000     # above this -> HUMAN

# Confidence threshold below which we escalate one tier
LOW_CONFIDENCE_THRESHOLD = 0.5


def select_model_tier(
    task_type: TaskType | str,
    risk_level: str = "low",          # "low", "medium", "high"
    dollar_exposure: float = 0.0,
    compliance_sensitive: bool = False,
    confidence: Optional[float] = None,
    missing_evidence: bool = False,
) -> ModelTier:
    """Select the appropriate model tier for a given task.

    Rules:
    - deterministic_update -> NO_MODEL (tier 0)
    - simple tasks -> SMALL (tier 1)
    - customer-facing drafts -> MEDIUM (tier 2), escalate if risk >= medium
    - procurement -> MEDIUM or STRONG by dollar exposure
    - compliance -> STRONG or HUMAN by dollar exposure
    - binding commitments -> always HUMAN
    - low confidence -> escalate one tier
    - missing evidence -> escalate one tier (capped at HUMAN)
    """
    if isinstance(task_type, str):
        task_type = TaskType(task_type)

    # --- Base tier by task type ---
    if task_type == TaskType.DETERMINISTIC_UPDATE:
        tier = ModelTier.NO_MODEL

    elif task_type in (
        TaskType.SIMPLE_CLASSIFICATION,
        TaskType.STRUCTURED_EXTRACTION,
    ):
        tier = ModelTier.SMALL

    elif task_type == TaskType.CUSTOMER_MESSAGE_DRAFT:
        tier = ModelTier.MEDIUM if risk_level == "low" else ModelTier.STRONG

    elif task_type == TaskType.APPROVAL_CARD_SUMMARY:
        tier = ModelTier.MEDIUM

    elif task_type == TaskType.OPPORTUNITY_SCORING:
        tier = ModelTier.MEDIUM if dollar_exposure < 5000 else ModelTier.STRONG

    elif task_type == TaskType.PROCUREMENT_ANALYSIS:
        if dollar_exposure >= PROCUREMENT_DOLLAR_THRESHOLD:
            tier = ModelTier.STRONG
        else:
            tier = ModelTier.MEDIUM

    elif task_type == TaskType.NEGOTIATION_PREP:
        if dollar_exposure >= NEGOTIATION_DOLLAR_THRESHOLD:
            tier = ModelTier.HUMAN
        else:
            tier = ModelTier.STRONG

    elif task_type == TaskType.COMPLIANCE_SENSITIVE_ACTION:
        if compliance_sensitive and dollar_exposure >= COMPLIANCE_DOLLAR_THRESHOLD:
            tier = ModelTier.HUMAN
        elif compliance_sensitive or dollar_exposure >= COMPLIANCE_DOLLAR_THRESHOLD:
            tier = ModelTier.STRONG
        else:
            tier = ModelTier.MEDIUM

    elif task_type == TaskType.BINDING_COMMITMENT:
        tier = ModelTier.HUMAN

    else:
        tier = ModelTier.MEDIUM  # safe default

    # --- Escalation rules ---
    # Deterministic tasks NEVER escalate — they require no model at all.
    if task_type == TaskType.DETERMINISTIC_UPDATE:
        return tier

    escalations = 0

    if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
        escalations += 1

    if missing_evidence:
        escalations += 1

    if risk_level == "high" and tier < ModelTier.STRONG:
        escalations += 1

    # Apply escalations (capped at HUMAN)
    for _ in range(escalations):
        if tier == ModelTier.HUMAN:
            break
        tier = ModelTier(tier.value + 1)

    return tier
