"""Autonomy scorecard service.

Tracks per-business metrics about proposals, approvals, executions,
violations, and confidence. Used by operators to decide how much
autonomy to grant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from chromagora_api.db.tenant import get_backend_supabase, get_business_tenant_id


@dataclass
class AutonomyScorecard:
    business_id: str
    generated_at: str = ""
    total_proposals: int = 0
    approvals_required: int = 0
    approvals_accepted: int = 0
    approvals_rejected: int = 0
    dry_run_executions: int = 0
    real_executions: int = 0
    blocked_by_policy: int = 0
    violations: int = 0
    failures: int = 0
    avg_confidence: float = 0.0
    total_value_proposed: float = 0.0
    total_value_approved: float = 0.0
    autonomy_level_current: int = 1
    autonomy_level_recommended: int = 1
    escalation_rate: float = 0.0
    total_envelopes: int = 0
    avg_autonomy: float = 0.0
    max_autonomy: int = 0
    active_tools: int = 0
    total_tools: int = 0
    notes: list[str] = field(default_factory=list)


def get_supabase():
    """Compatibility seam for tests; production uses the backend admin client."""
    return get_backend_supabase()


def get_autonomy_scorecard(business_id: UUID) -> AutonomyScorecard:
    """Generate autonomy scorecard for a business by querying Supabase."""
    try:
        sb = get_supabase()
    except RuntimeError:
        scorecard = AutonomyScorecard(business_id=str(business_id))
        scorecard.notes.append("Database not available")
        return scorecard
    if not sb:
        scorecard = AutonomyScorecard(business_id=str(business_id))
        scorecard.notes.append("Database not available")
        return scorecard

    bid = str(business_id)
    if not get_business_tenant_id(bid, sb):
        raise RuntimeError("Business not found")

    now = datetime.now(timezone.utc).isoformat()
    scorecard = AutonomyScorecard(
        business_id=bid,
        generated_at=now,
    )

    # Action proposals
    proposals_resp = (
        sb.table("action_proposals")
        .select("id, status, confidence, risk_level")
        .eq("business_id", bid)
        .execute()
    )
    proposals = proposals_resp.data or []
    scorecard.total_proposals = len(proposals)

    for p in proposals:
        if p.get("status") == "approval_required":
            scorecard.approvals_required += 1
        elif p.get("status") == "approved":
            scorecard.approvals_accepted += 1
        elif p.get("status") == "rejected":
            scorecard.approvals_rejected += 1
        elif p.get("status") == "blocked":
            scorecard.blocked_by_policy += 1

    # Average confidence
    confidences = [p["confidence"] for p in proposals if p.get("confidence") is not None]
    if confidences:
        scorecard.avg_confidence = round(sum(confidences) / len(confidences), 3)

    # Action executions
    executions_resp = (
        sb.table("action_executions")
        .select("id, result_status, reversibility")
        .eq("business_id", bid)
        .execute()
    )
    executions = executions_resp.data or []
    for e in executions:
        if e.get("result_status") == "dry_run":
            scorecard.dry_run_executions += 1
        elif e.get("result_status") == "success":
            scorecard.real_executions += 1
        elif e.get("result_status") == "failed":
            scorecard.failures += 1

    # Events for violations
    violations_resp = (
        sb.table("events")
        .select("id")
        .eq("business_id", bid)
        .eq("event_type", "policy.violation_detected")
        .execute()
    )
    scorecard.violations = len(violations_resp.data or [])

    # Escalation rate
    if scorecard.total_proposals > 0:
        scorecard.escalation_rate = round(
            scorecard.approvals_required / scorecard.total_proposals, 3
        )

    # Autonomy level recommendation
    scorecard.autonomy_level_current = _get_current_autonomy_level(sb, bid)
    _populate_frontend_summary(sb, bid, scorecard)
    scorecard.autonomy_level_recommended = _recommend_autonomy_level(scorecard)
    scorecard.notes = _generate_notes(scorecard)

    return scorecard


def _get_current_autonomy_level(sb, bid: str) -> int:
    """Get the current max autonomy level from active authority envelopes."""
    resp = (
        sb.table("authority_envelopes")
        .select("autonomy_level")
        .eq("business_id", bid)
        .eq("is_active", True)
        .execute()
    )
    envelopes = resp.data or []
    if not envelopes:
        return 1
    return max(e["autonomy_level"] for e in envelopes)


def _populate_frontend_summary(sb, bid: str, sc: AutonomyScorecard) -> None:
    """Populate the compact metrics used by the business detail UI."""
    env_resp = (
        sb.table("authority_envelopes")
        .select("autonomy_level, is_active")
        .eq("business_id", bid)
        .execute()
    )
    envelopes = env_resp.data or []
    active_levels = [
        int(env.get("autonomy_level") or 0)
        for env in envelopes
        if env.get("is_active", True)
    ]
    sc.total_envelopes = len(envelopes)
    sc.max_autonomy = max(active_levels, default=0)
    sc.avg_autonomy = round(sum(active_levels) / len(active_levels), 1) if active_levels else 0.0

    tools_resp = (
        sb.table("business_tool_permissions")
        .select("id, is_enabled")
        .eq("business_id", bid)
        .execute()
    )
    tools = tools_resp.data or []
    sc.total_tools = len(tools)
    sc.active_tools = len([tool for tool in tools if tool.get("is_enabled")])


def _recommend_autonomy_level(sc: AutonomyScorecard) -> int:
    """Recommend an autonomy level based on scorecard metrics.

    Rules:
    - Start at level 1 (observe/analyze)
    - If >20 proposals, >0.7 avg confidence, <0.1 escalation rate, 0 violations -> level 2
    - If >50 proposals, >0.8 avg confidence, <0.05 escalation rate, 0 violations, >10 real executions -> level 3
    - If >100 proposals, >0.85 avg confidence, <0.02 escalation rate, 0 violations, >25 real executions -> level 4
    - Level 5+ never recommended automatically
    """
    if sc.total_proposals < 20:
        return max(1, sc.autonomy_level_current)

    if sc.violations > 0:
        return max(1, sc.autonomy_level_current - 1)

    if (
        sc.total_proposals >= 100
        and sc.avg_confidence >= 0.85
        and sc.escalation_rate <= 0.02
        and sc.real_executions >= 25
    ):
        return 4

    if (
        sc.total_proposals >= 50
        and sc.avg_confidence >= 0.8
        and sc.escalation_rate <= 0.05
        and sc.real_executions >= 10
    ):
        return 3

    if (
        sc.total_proposals >= 20
        and sc.avg_confidence >= 0.7
        and sc.escalation_rate <= 0.1
    ):
        return 2

    return max(1, sc.autonomy_level_current)


def _generate_notes(sc: AutonomyScorecard) -> list[str]:
    """Generate human-readable notes about the scorecard."""
    notes = []

    if sc.violations > 0:
        notes.append(f"⚠ {sc.violations} policy violation(s) detected — review before increasing autonomy")

    if sc.escalation_rate > 0.3:
        notes.append(f"High escalation rate ({sc.escalation_rate:.0%}) — proposals frequently require approval")

    if sc.avg_confidence < 0.5 and sc.total_proposals > 5:
        notes.append("Low average confidence — agents may need better context or model upgrades")

    if sc.failures > sc.real_executions and sc.real_executions > 0:
        notes.append("More failures than successes — review tool configurations")

    if sc.autonomy_level_recommended > sc.autonomy_level_current:
        notes.append(
            f"Recommended autonomy level increase: {sc.autonomy_level_current} → {sc.autonomy_level_recommended}"
        )
    elif sc.autonomy_level_recommended < sc.autonomy_level_current:
        notes.append(
            f"Recommended autonomy level decrease: {sc.autonomy_level_current} → {sc.autonomy_level_recommended}"
        )
    else:
        notes.append(f"Autonomy level {sc.autonomy_level_current} appears appropriate")

    return notes


def scorecard_to_dict(sc: AutonomyScorecard) -> dict[str, Any]:
    """Convert scorecard to dict for API response."""
    return {
        "business_id": sc.business_id,
        "generated_at": sc.generated_at,
        "total_proposals": sc.total_proposals,
        "approvals_required": sc.approvals_required,
        "approvals_accepted": sc.approvals_accepted,
        "approvals_rejected": sc.approvals_rejected,
        "dry_run_executions": sc.dry_run_executions,
        "real_executions": sc.real_executions,
        "blocked_by_policy": sc.blocked_by_policy,
        "violations": sc.violations,
        "failures": sc.failures,
        "avg_confidence": sc.avg_confidence,
        "total_value_proposed": sc.total_value_proposed,
        "total_value_approved": sc.total_value_approved,
        "autonomy_level_current": sc.autonomy_level_current,
        "autonomy_level_recommended": sc.autonomy_level_recommended,
        "escalation_rate": sc.escalation_rate,
        "total_envelopes": sc.total_envelopes,
        "avg_autonomy": sc.avg_autonomy,
        "max_autonomy": sc.max_autonomy,
        "active_tools": sc.active_tools,
        "total_tools": sc.total_tools,
        "notes": sc.notes,
    }
