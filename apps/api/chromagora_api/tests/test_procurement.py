"""Tests for Procurement Scout v0."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from chromagora_api.services.procurement_agent import evaluate_opportunity, _score_fit
from chromagora_schemas.opportunities import (
    OpportunityCreate,
    OpportunityStatus,
    OpportunityResponse,
)


class TestScoreFit:
    def test_all_criteria_met(self):
        data = {
            "service_type": "roofing",
            "location": "Austin",
            "deadline_at": "2026-07-01T00:00:00Z",
            "estimated_value_max": 50000,
            "required_documents": ["insurance", "license"],
        }
        result = _score_fit(data)
        assert abs(result["fit_score"] - 0.8) < 0.01
        assert len(result["factors"]) == 5

    def test_no_criteria_met(self):
        data = {
            "service_type": "",
            "location": "",
        }
        result = _score_fit(data)
        assert result["fit_score"] == 0.0
        assert len(result["factors"]) == 0

    def test_partial_match(self):
        data = {
            "service_type": "roofing",
            "location": "",
            "deadline_at": "2026-07-01T00:00:00Z",
        }
        result = _score_fit(data)
        assert result["fit_score"] == 0.4
        assert result["factors"]["service_match"] is True
        assert result["factors"]["has_deadline"] is True

    def test_score_capped_at_1(self):
        data = {
            "service_type": "roofing",
            "location": "Austin",
            "deadline_at": "2026-07-01T00:00:00Z",
            "estimated_value_max": 50000,
            "estimated_value_min": 10000,
            "required_documents": ["a", "b", "c"],
        }
        result = _score_fit(data)
        assert result["fit_score"] <= 1.0


class TestOpportunityCreate:
    def test_create(self):
        opp = OpportunityCreate(
            business_id=uuid4(),
            opportunity_type="government_contract",
            source_name="SAM.gov",
            title="Roof replacement",
        )
        assert opp.status == OpportunityStatus.DETECTED
        assert opp.required_documents == []

    def test_default_status(self):
        opp = OpportunityCreate(
            business_id=uuid4(),
            opportunity_type="rfp",
            source_name="Vendor",
            title="Test",
        )
        assert opp.status == OpportunityStatus.DETECTED


class TestOpportunityStatus:
    def test_all_statuses(self):
        assert OpportunityStatus.DETECTED.value == "detected"
        assert OpportunityStatus.QUALIFIED.value == "qualified"
        assert OpportunityStatus.WON.value == "won"
        assert OpportunityStatus.LOST.value == "lost"


class TestEvaluateOpportunity:
    @patch("chromagora_api.services.procurement_agent.start_agent_run")
    @patch("chromagora_api.services.procurement_agent.request_tool_execution")
    @patch("chromagora_api.services.procurement_agent.complete_agent_run")
    def test_successful_evaluation(
        self, mock_complete, mock_tool, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_tool.return_value = {"status": "dry_run"}
        mock_complete.return_value = MagicMock()

        result = evaluate_opportunity(
            tenant_id=uuid4(),
            business_id=uuid4(),
            opportunity_type="rfp",
            source_name="City of Austin",
            title="Roof replacement project",
            description="Replace 5000 sq ft roof",
            service_type="roofing",
            estimated_value_max=50000,
        )

        assert result["status"] == "completed"
        assert result["fit_score"] >= 0.4
        assert "recommended_next_action" in result
        mock_tool.assert_called_once()
        mock_complete.assert_called_once()

    @patch("chromagora_api.services.procurement_agent.start_agent_run")
    def test_agent_run_failure(self, mock_start):
        mock_start.return_value = None

        result = evaluate_opportunity(
            tenant_id=uuid4(),
            business_id=uuid4(),
            opportunity_type="rfp",
            source_name="Test",
            title="Test",
        )

        assert result["status"] == "failed"
