"""Deterministic eval fixtures — verify system behavior without real LLM.

Chapter 18.2: Fixed scenarios with expected outcomes. No mock LLM, no external
calls. Pure deterministic logic verification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Eval result types
# ---------------------------------------------------------------------------

class EvalResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class EvalCaseResult:
    name: str
    result: EvalResult
    expected: Any
    actual: Any
    duration_ms: int = 0
    detail: str = ""


@dataclass
class EvalSuiteResult:
    suite_name: str
    cases: list[EvalCaseResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.result == EvalResult.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.cases if c.result == EvalResult.FAIL)

    @property
    def total(self) -> int:
        return len(self.cases)


# ---------------------------------------------------------------------------
# Eval fixtures
# ---------------------------------------------------------------------------

def run_all_evals() -> list[EvalSuiteResult]:
    """Run all eval suites and return results."""
    suites = [
        _eval_review_request_allowed(),
        _eval_review_request_approval_required(),
        _eval_stale_quote_allowed(),
        _eval_stale_quote_approval_required(),
        _eval_opportunity_high_fit(),
        _eval_opportunity_low_fit(),
        _eval_binding_execution_blocked(),
        _eval_low_confidence_escalates(),
        _eval_forbidden_claim_blocks_message(),
    ]
    return suites


def _eval_review_request_allowed() -> EvalSuiteResult:
    """Eval 1: Review request with low risk and high reputation should be auto-allowed."""
    suite = EvalSuiteResult(suite_name="review_request_allowed")

    # A review request from a well-rated business with low amount
    # should pass policy kernel without approval
    from chromagora_api.services.policy_kernel import evaluate_proposal
    from chromagora_schemas.authority import ProposalCreate

    proposal = ProposalCreate(
        business_id=uuid4(),
        proposed_by_type="agent",
        proposed_by_id=uuid4(),
        action_type="send_review_request",
        title="Request review from customer",
        description="Auto-generated review request after job completion",
        target_system="email",
        proposed_payload={"customer_name": "Test Customer", "job_summary": "Test job"},
        expected_value=50.0,
        confidence=0.9,
        risk_level="low",
        autonomy_level_required=0,
    )

    decision = evaluate_proposal(proposal)

    suite.cases.append(EvalCaseResult(
        name="low_risk_auto_allowed",
        result=EvalResult.PASS if decision.get("decision") == "allowed" else EvalResult.FAIL,
        expected="allowed",
        actual=decision.get("decision"),
    ))

    return suite


def _eval_review_request_approval_required() -> EvalSuiteResult:
    """Eval 2: Review request with high risk should require approval."""
    suite = EvalSuiteResult(suite_name="review_request_approval_required")

    from chromagora_api.services.policy_kernel import evaluate_proposal
    from chromagora_schemas.authority import ProposalCreate

    proposal = ProposalCreate(
        business_id=uuid4(),
        proposed_by_type="agent",
        proposed_by_id=uuid4(),
        action_type="send_review_request",
        title="Request review with incentive",
        description="Review request offering discount",
        target_system="email",
        proposed_payload={"customer_name": "Test", "incentive": "10% off"},
        expected_value=500.0,
        confidence=0.5,
        risk_level="high",
        autonomy_level_required=2,
    )

    decision = evaluate_proposal(proposal)

    suite.cases.append(EvalCaseResult(
        name="high_risk_requires_approval",
        result=EvalResult.PASS if decision.get("decision") == "approval_required" else EvalResult.FAIL,
        expected="approval_required",
        actual=decision.get("decision"),
    ))

    return suite


def _eval_stale_quote_allowed() -> EvalSuiteResult:
    """Eval 3: Stale quote follow-up within safe parameters should be allowed."""
    suite = EvalSuiteResult(suite_name="stale_quote_allowed")

    from chromagora_api.services.policy_kernel import evaluate_proposal
    from chromagora_schemas.authority import ProposalCreate

    proposal = ProposalCreate(
        business_id=uuid4(),
        proposed_by_type="agent",
        proposed_by_id=uuid4(),
        action_type="stale_quote_followup",
        title="Follow up on stale quote",
        description="Quote sent 12 days ago, no response",
        target_system="email",
        proposed_payload={
            "customer_name": "Test Customer",
            "quote_amount": 200.0,
            "days_stale": 12,
        },
        expected_value=200.0,
        confidence=0.8,
        risk_level="low",
        autonomy_level_required=0,
    )

    decision = evaluate_proposal(proposal)

    suite.cases.append(EvalCaseResult(
        name="stale_quote_auto_allowed",
        result=EvalResult.PASS if decision.get("decision") == "allowed" else EvalResult.FAIL,
        expected="allowed",
        actual=decision.get("decision"),
    ))

    return suite


def _eval_stale_quote_approval_required() -> EvalSuiteResult:
    """Eval 4: Stale quote follow-up with high value should require approval."""
    suite = EvalSuiteResult(suite_name="stale_quote_approval_required")

    from chromagora_api.services.policy_kernel import evaluate_proposal
    from chromagora_schemas.authority import ProposalCreate

    proposal = ProposalCreate(
        business_id=uuid4(),
        proposed_by_type="agent",
        proposed_by_id=uuid4(),
        action_type="stale_quote_followup",
        title="Follow up on high-value stale quote",
        description="Quote sent 12 days ago, high value",
        target_system="email",
        proposed_payload={
            "customer_name": "Test Customer",
            "quote_amount": 50000.0,
            "days_stale": 12,
        },
        expected_value=50000.0,
        confidence=0.6,
        risk_level="medium",
        autonomy_level_required=2,
    )

    decision = evaluate_proposal(proposal)

    suite.cases.append(EvalCaseResult(
        name="high_value_stale_quote_requires_approval",
        result=EvalResult.PASS if decision.get("decision") == "approval_required" else EvalResult.FAIL,
        expected="approval_required",
        actual=decision.get("decision"),
    ))

    return suite


def _eval_opportunity_high_fit() -> EvalSuiteResult:
    """Eval 5: High-fit opportunity should score above threshold."""
    suite = EvalSuiteResult(suite_name="opportunity_high_fit")

    from chromagora_api.services.procurement_agent import score_opportunity_fit

    score = score_opportunity_fit(
        service_types=["plumbing", "heating"],
        capacity_available=True,
        margin_estimate=0.35,
        strategic_alignment=0.8,
    )

    suite.cases.append(EvalCaseResult(
        name="high_fit_above_threshold",
        result=EvalResult.PASS if score >= 0.6 else EvalResult.FAIL,
        expected=">= 0.6",
        actual=score,
    ))

    return suite


def _eval_opportunity_low_fit() -> EvalSuiteResult:
    """Eval 6: Low-fit opportunity should score below threshold."""
    suite = EvalSuiteResult(suite_name="opportunity_low_fit")

    from chromagora_api.services.procurement_agent import score_opportunity_fit

    score = score_opportunity_fit(
        service_types=["specialist_electrical"],
        capacity_available=False,
        margin_estimate=0.05,
        strategic_alignment=0.1,
    )

    suite.cases.append(EvalCaseResult(
        name="low_fit_below_threshold",
        result=EvalResult.PASS if score < 0.4 else EvalResult.FAIL,
        expected="< 0.4",
        actual=score,
    ))

    return suite


def _eval_binding_execution_blocked() -> EvalSuiteResult:
    """Eval 7: Binding execution without approval should be blocked."""
    suite = EvalSuiteResult(suite_name="binding_execution_blocked")

    from chromagora_api.services.policy_kernel import check_execution_allowed

    allowed = check_execution_allowed(
        action_type="send_email",
        has_approval=False,
        is_binding=True,
    )

    suite.cases.append(EvalCaseResult(
        name="binding_without_approval_blocked",
        result=EvalResult.PASS if not allowed else EvalResult.FAIL,
        expected=False,
        actual=allowed,
    ))

    return suite


def _eval_low_confidence_escalates() -> EvalSuiteResult:
    """Eval 8: Low confidence proposal should escalate to approval."""
    suite = EvalSuiteResult(suite_name="low_confidence_escalates")

    from chromagora_api.services.policy_kernel import evaluate_proposal
    from chromagora_schemas.authority import ProposalCreate

    proposal = ProposalCreate(
        business_id=uuid4(),
        proposed_by_type="agent",
        proposed_by_id=uuid4(),
        action_type="send_email",
        title="Low confidence action",
        description="Action with very low confidence score",
        target_system="email",
        proposed_payload={},
        expected_value=100.0,
        confidence=0.15,
        risk_level="medium",
        autonomy_level_required=1,
    )

    decision = evaluate_proposal(proposal)

    suite.cases.append(EvalCaseResult(
        name="low_confidence_escalates",
        result=EvalResult.PASS if decision.get("decision") == "approval_required" else EvalResult.FAIL,
        expected="approval_required",
        actual=decision.get("decision"),
    ))

    return suite


def _eval_forbidden_claim_blocks_message() -> EvalSuiteResult:
    """Eval 9: Forbidden claim in message draft should block execution."""
    suite = EvalSuiteResult(suite_name="forbidden_claim_blocks_message")

    from chromagora_api.services.policy_kernel import check_claim_allowed

    # A forbidden claim (e.g., "guaranteed results") should be blocked
    allowed = check_claim_allowed(
        claim_text="We guarantee 100% satisfaction",
        claim_type="guarantee",
    )

    suite.cases.append(EvalCaseResult(
        name="forbidden_claim_blocked",
        result=EvalResult.PASS if not allowed else EvalResult.FAIL,
        expected=False,
        actual=allowed,
    ))

    return suite
