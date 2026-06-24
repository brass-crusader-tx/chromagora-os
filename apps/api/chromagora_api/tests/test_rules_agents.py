"""Tests for Rules-Based Agents v0 (Reputation and Sales)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from chromagora_api.services.reputation_agent import run_review_request
from chromagora_api.services.sales_agent import run_stale_quote_followup


class TestReputationAgent:
    @patch("chromagora_api.services.reputation_agent.start_agent_run")
    @patch("chromagora_api.services.reputation_agent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.reputation_agent.request_tool_execution")
    @patch("chromagora_api.services.reputation_agent.complete_agent_run")
    def test_successful_review_request(
        self, mock_complete, mock_tool, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())
        mock_tool.return_value = {"status": "dry_run"}
        mock_complete.return_value = MagicMock()

        result = run_review_request(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="John Doe",
            customer_contact="john@example.com",
            job_summary="Built a deck",
            completed_at="2026-06-20T10:00:00Z",
        )

        assert result["status"] == "completed"
        assert result["tool_name"] == "reputation.queue_review_request"
        assert result["tool_status"] == "dry_run"
        mock_tool.assert_called_once()
        mock_complete.assert_called_once()

    @patch("chromagora_api.services.reputation_agent.start_agent_run")
    @patch("chromagora_api.services.reputation_agent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.reputation_agent.fail_agent_run")
    def test_missing_customer_name(
        self, mock_fail, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())

        result = run_review_request(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="",
            customer_contact="john@example.com",
            job_summary="Built a deck",
            completed_at="2026-06-20T10:00:00Z",
        )

        assert result["status"] == "failed"
        assert "errors" in result
        mock_fail.assert_called_once()

    @patch("chromagora_api.services.reputation_agent.start_agent_run")
    def test_agent_run_start_failure(self, mock_start):
        mock_start.return_value = None

        result = run_review_request(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="John",
            customer_contact="john@example.com",
            job_summary="Deck",
            completed_at="2026-06-20T10:00:00Z",
        )

        assert result["status"] == "failed"
        assert "Failed to start" in result["error"]


class TestSalesAgent:
    @patch("chromagora_api.services.sales_agent.start_agent_run")
    @patch("chromagora_api.services.sales_agent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.sales_agent.request_tool_execution")
    @patch("chromagora_api.services.sales_agent.complete_agent_run")
    def test_stale_quote_creates_followup(
        self, mock_complete, mock_tool, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())
        mock_tool.return_value = {"status": "dry_run"}
        mock_complete.return_value = MagicMock()

        from datetime import datetime, timedelta, timezone
        stale_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

        result = run_stale_quote_followup(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="Jane Doe",
            customer_contact="jane@example.com",
            service_type="Roofing",
            quote_sent_at=stale_date,
            quote_amount=5000.0,
        )

        assert result["status"] == "completed"
        assert result["is_stale"] is True
        assert result["tool_name"] == "crm.create_followup_task"
        mock_tool.assert_called_once()
        mock_complete.assert_called_once()

    @patch("chromagora_api.services.sales_agent.start_agent_run")
    @patch("chromagora_api.services.sales_agent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.sales_agent.complete_agent_run")
    def test_not_stale_no_action(
        self, mock_complete, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())
        mock_complete.return_value = MagicMock()

        from datetime import datetime, timedelta, timezone
        recent_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        result = run_stale_quote_followup(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="Jane Doe",
            customer_contact="jane@example.com",
            service_type="Roofing",
            quote_sent_at=recent_date,
        )

        assert result["status"] == "completed"
        assert result["action"] == "none"
        assert result["reason"] == "not_stale"

    @patch("chromagora_api.services.sales_agent.start_agent_run")
    @patch("chromagora_api.services.sales_agent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.sales_agent.fail_agent_run")
    def test_missing_required_fields(
        self, mock_fail, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())

        result = run_stale_quote_followup(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="",
            customer_contact="",
            service_type="",
            quote_sent_at="2026-01-01T00:00:00Z",
        )

        assert result["status"] == "failed"
        assert "errors" in result
        mock_fail.assert_called_once()

    @patch("chromagora_api.services.sales_agent.start_agent_run")
    def test_agent_run_start_failure(self, mock_start):
        mock_start.return_value = None

        result = run_stale_quote_followup(
            tenant_id=uuid4(),
            business_id=uuid4(),
            customer_name="Jane",
            customer_contact="jane@example.com",
            service_type="Roofing",
            quote_sent_at="2026-01-01T00:00:00Z",
        )

        assert result["status"] == "failed"
