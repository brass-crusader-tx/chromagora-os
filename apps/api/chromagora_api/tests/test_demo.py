"""Tests for demo simulation endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from chromagora_api.routes.demo import router


class TestDemoReviewRequestSimulation:
    @patch("chromagora_api.routes.demo.get_supabase")
    @patch("chromagora_api.routes.demo.run_review_request")
    def test_successful(self, mock_agent, mock_sb):
        mock_sb.return_value = MagicMock()
        mock_biz = MagicMock()
        mock_biz.data = [{"tenant_id": str(uuid4())}]
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_biz

        mock_event = MagicMock()
        mock_event.data = [{"id": "evt-123"}]
        mock_sb.return_value.table.return_value.insert.return_value.execute.return_value = mock_event

        mock_agent.return_value = {"status": "completed", "action": "test"}

        # Use TestClient to call the endpoint
        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post("/demo/review-request-simulation", json={
            "business_id": str(uuid4()),
            "customer_name": "Test Customer",
            "customer_contact": "test@example.com",
            "job_summary": "Fixed the roof",
            "completed_at": "2026-06-24T10:00:00Z",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert "event_id" in data
        assert "agent_result" in data

    @patch("chromagora_api.routes.demo.get_supabase")
    def test_no_database(self, mock_sb):
        mock_sb.return_value = None

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post("/demo/review-request-simulation", json={
            "business_id": str(uuid4()),
            "customer_name": "Test",
            "customer_contact": "test@test.com",
            "job_summary": "Test job",
            "completed_at": "2026-06-24T10:00:00Z",
        })

        assert resp.status_code == 503


class TestDemoStaleQuoteSimulation:
    @patch("chromagora_api.routes.demo.get_supabase")
    @patch("chromagora_api.routes.demo.run_stale_quote_followup")
    def test_successful(self, mock_agent, mock_sb):
        mock_sb.return_value = MagicMock()
        mock_biz = MagicMock()
        mock_biz.data = [{"tenant_id": str(uuid4())}]
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_biz

        mock_event = MagicMock()
        mock_event.data = [{"id": "evt-456"}]
        mock_sb.return_value.table.return_value.insert.return_value.execute.return_value = mock_event

        mock_agent.return_value = {"status": "completed"}

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post("/demo/stale-quote-simulation", json={
            "business_id": str(uuid4()),
            "customer_name": "Test",
            "customer_contact": "test@test.com",
            "service_type": "roofing",
            "quote_sent_at": "2026-06-10T10:00:00Z",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"


class TestDemoOpportunitySimulation:
    @patch("chromagora_api.routes.demo.get_supabase")
    @patch("chromagora_api.routes.demo.evaluate_opportunity")
    def test_successful(self, mock_agent, mock_sb):
        mock_sb.return_value = MagicMock()
        mock_biz = MagicMock()
        mock_biz.data = [{"tenant_id": str(uuid4())}]
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_biz

        mock_event = MagicMock()
        mock_event.data = [{"id": "evt-789"}]
        mock_sb.return_value.table.return_value.insert.return_value.execute.return_value = mock_event

        mock_agent.return_value = {"status": "completed", "fit_score": 0.7}

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post("/demo/opportunity-simulation", json={
            "business_id": str(uuid4()),
            "opportunity_type": "rfp",
            "source_name": "City of Austin",
            "title": "Roof replacement",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
