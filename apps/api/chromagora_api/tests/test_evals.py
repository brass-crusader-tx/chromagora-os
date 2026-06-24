"""Tests for deterministic eval fixtures (Chapter 18.2)."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from chromagora_api.services.eval_runner import (
    run_all_evals,
    EvalResult,
)
from chromagora_api.services.policy_kernel import (
    check_execution_allowed,
    check_claim_allowed,
)
from chromagora_api.services.procurement_agent import score_opportunity_fit


class TestEvalRunner:
    @patch("chromagora_api.services.policy_kernel._get_supabase")
    def test_all_evals_run(self, mock_sb):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp
        mock_sb.return_value = mock_client

        suites = run_all_evals()
        assert len(suites) >= 5
        for suite in suites:
            assert suite.total > 0

    @patch("chromagora_api.services.policy_kernel._get_supabase")
    def test_evals_have_results(self, mock_sb):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp
        mock_sb.return_value = mock_client

        suites = run_all_evals()
        for suite in suites:
            for case in suite.cases:
                assert case.result in (EvalResult.PASS, EvalResult.FAIL, EvalResult.SKIP)


class TestCheckExecutionAllowed:
    def test_binding_without_approval_blocked(self):
        assert check_execution_allowed("send_email", has_approval=False, is_binding=True) is False

    def test_binding_with_approval_allowed(self):
        assert check_execution_allowed("send_email", has_approval=True, is_binding=True) is True

    def test_non_binding_allowed(self):
        assert check_execution_allowed("send_email", has_approval=False, is_binding=False) is True


class TestCheckClaimAllowed:
    def test_forbidden_guarantee(self):
        assert check_claim_allowed("We guarantee 100% satisfaction") is False

    def test_forbidden_promise(self):
        assert check_claim_allowed("We promise results") is False

    def test_allowed_normal_text(self):
        assert check_claim_allowed("Quality service at competitive prices") is True

    def test_forbidden_claim_type(self):
        assert check_claim_allowed("Great service", claim_type="guarantee") is False


class TestScoreOpportunityFit:
    def test_high_fit(self):
        score = score_opportunity_fit(
            service_types=["plumbing", "heating"],
            capacity_available=True,
            margin_estimate=0.35,
            strategic_alignment=0.8,
        )
        assert score >= 0.6

    def test_low_fit(self):
        score = score_opportunity_fit(
            service_types=["specialist_electrical"],
            capacity_available=False,
            margin_estimate=0.05,
            strategic_alignment=0.1,
        )
        assert score < 0.4

    def test_score_bounded(self):
        score = score_opportunity_fit(
            service_types=["a", "b", "c"],
            capacity_available=True,
            margin_estimate=1.0,
            strategic_alignment=1.0,
        )
        assert score <= 1.0
        assert score >= 0.0
