"""Policy Kernel evaluator — deterministic policy enforcement."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from chromagora_schemas.authority import (
    AutonomyLevel,
    PolicyDecision,
)
from chromagora_schemas.context import ModelTier
from chromagora_api.services.token_budget import select_model_tier

logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.db import get_supabase
    return get_supabase()


def _load_active_envelopes(business_id: UUID) -> list[dict]:
    """Load active authority envelopes for a business."""
    sb = _get_supabase()
    try:
        resp = (
            sb.table("authority_envelopes")
            .select("*")
            .eq("business_id", str(business_id))
            .eq("is_active", True)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        logger.warning("Failed to load authority envelopes: %s", exc)
        return []


def _load_active_compliance_rules(
    tenant_id: UUID,
    business_id: Optional[UUID],
    action_type: str,
) -> list[dict]:
    """Load active compliance rules matching the action type."""
    sb = _get_supabase()
    try:
        query = (
            sb.table("compliance_rules")
            .select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("is_active", True)
        )
        if business_id:
            # Rules can be tenant-wide (business_id is null) or business-specific
            query = query.or_(f"business_id.is.null,business_id.eq.{business_id})")
        if action_type:
            query = query.or_(
                f"applies_to_action_type.is.null,applies_to_action_type.eq.{action_type}"
            )
        resp = query.execute()
        return resp.data or []
    except Exception as exc:
        logger.warning("Failed to load compliance rules: %s", exc)
        return []


def _envelope_matches(
    envelope: dict,
    actor_type: str,
    action_type: str,
    tool_name: str,
) -> bool:
    """Check if an envelope matches the actor/action context.

    Null scope = wildcard (matches anything).
    """
    agent_scope = envelope.get("agent_scope")
    if agent_scope is not None and agent_scope != actor_type:
        return False

    action_type_scope = envelope.get("action_type_scope")
    if action_type_scope is not None and action_type_scope != action_type:
        return False

    # tool_scope is informational; actual tool permission is checked by ToolBroker
    return True


def evaluate_action_policy(
    business_id: UUID,
    actor_type: str,
    actor_id: Optional[UUID],
    action_type: str,
    target_system: str,
    autonomy_level_requested: int,
    dollar_exposure: float = 0.0,
    risk_level: str = "low",
    confidence: Optional[float] = None,
    compliance_sensitive: bool = False,
    payload_json: Optional[dict[str, Any]] = None,
    tenant_id: Optional[UUID] = None,
) -> PolicyDecision:
    """Evaluate whether an action is allowed, requires approval, or is denied.

    Rules:
    1. Load active envelopes via Supabase
    2. Null scope = wildcard
    3. No match -> require approval
    4. Autonomy exceeds -> require approval
    5. Dollar exceeds -> require approval
    6. Low confidence -> escalate
    7. Compliance sensitive -> require approval unless explicit
    8. Level 6 -> always require approval
    9. Forbidden conditions -> deny
    10. Include model tier recommendation from TokenBudgetPolicy
    """
    denial_reasons: list[str] = []
    approval_reasons: list[str] = []
    matched_envelope_ids: list[UUID] = []

    # Load envelopes
    envelopes = _load_active_envelopes(business_id)

    # Find matching envelopes
    matching = [
        env for env in envelopes
        if _envelope_matches(env, actor_type, action_type, target_system)
    ]

    if not matching:
        approval_reasons.append("No matching authority envelope found")

    # Check each matching envelope
    max_autonomy_allowed = AutonomyLevel.OBSERVE
    max_dollar = float("inf")

    for env in matching:
        env_id = UUID(env["id"])
        matched_envelope_ids.append(env_id)

        env_autonomy = env.get("autonomy_level", 0)
        if env_autonomy > max_autonomy_allowed.value:
            max_autonomy_allowed = AutonomyLevel(env_autonomy)

        env_max_dollar = env.get("max_dollar_exposure")
        if env_max_dollar is not None and env_max_dollar < max_dollar:
            max_dollar = float(env_max_dollar)

        # Rule 9: Forbidden conditions -> deny
        forbidden = env.get("forbidden_conditions_json", {})
        if forbidden:
            for key, value in forbidden.items():
                if payload_json and payload_json.get(key) == value:
                    denial_reasons.append(
                        f"Forbidden condition matched: {key}={value}"
                    )

    # Rule 4: Autonomy exceeds
    if autonomy_level_requested > max_autonomy_allowed.value:
        approval_reasons.append(
            f"Requested autonomy level {autonomy_level_requested} exceeds "
            f"maximum allowed {max_autonomy_allowed.value}"
        )

    # Rule 5: Dollar exceeds
    if dollar_exposure > 0 and max_dollar != float("inf") and dollar_exposure > max_dollar:
        approval_reasons.append(
            f"Dollar exposure ${dollar_exposure:,.2f} exceeds "
            f"maximum ${max_dollar:,.2f}"
        )

    # Rule 6: Low confidence -> escalate
    if confidence is not None and confidence < 0.5:
        approval_reasons.append(f"Low confidence ({confidence:.2f})")

    # Rule 7: Compliance sensitive
    if compliance_sensitive:
        approval_reasons.append("Action is compliance-sensitive")

    # Rule 8: Level 6 always requires approval
    if autonomy_level_requested >= 6:
        approval_reasons.append("Binding execution (level 6) always requires approval")

    # Load compliance rules
    compliance_ids: list[UUID] = []
    if tenant_id:
        rules = _load_active_compliance_rules(tenant_id, business_id, action_type)
        for rule in rules:
            compliance_ids.append(UUID(rule["id"]))
            config = rule.get("rule_config_json", {})
            if config.get("blocking"):
                denial_reasons.append(
                    f"Compliance rule '{rule.get('name')}' blocks this action"
                )

    # Determine decision
    if denial_reasons:
        decision = PolicyDecision(
            allowed=False,
            denied=True,
            denial_reasons=denial_reasons,
            matched_authority_envelope_ids=matched_envelope_ids,
            max_autonomy_level_allowed=max_autonomy_allowed,
            compliance_rule_ids=compliance_ids,
            decision_notes="Action denied by policy kernel",
        )
    elif approval_reasons:
        decision = PolicyDecision(
            allowed=False,
            requires_approval=True,
            approval_reasons=approval_reasons,
            matched_authority_envelope_ids=matched_envelope_ids,
            max_autonomy_level_allowed=max_autonomy_allowed,
            compliance_rule_ids=compliance_ids,
            decision_notes="Action requires approval",
        )
    else:
        decision = PolicyDecision(
            allowed=True,
            matched_authority_envelope_ids=matched_envelope_ids,
            max_autonomy_level_allowed=max_autonomy_allowed,
            compliance_rule_ids=compliance_ids,
            decision_notes="Action allowed",
        )

    # Rule 10: Model tier recommendation
    from chromagora_schemas.context import TaskType
    task_type_str = action_type if action_type else "deterministic_update"
    try:
        task_type = TaskType(task_type_str)
    except ValueError:
        task_type = TaskType.DETERMINISTIC_UPDATE

    recommended_tier = select_model_tier(
        task_type=task_type,
        risk_level=risk_level,
        dollar_exposure=dollar_exposure,
        compliance_sensitive=compliance_sensitive,
        confidence=confidence,
    )
    decision.model_tier_recommendation = recommended_tier.value

    return decision
