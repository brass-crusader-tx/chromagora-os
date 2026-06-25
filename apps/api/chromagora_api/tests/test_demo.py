"""Tests for demo simulation endpoints."""

from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from chromagora_api.main import app

_client = TestClient(app)

_FAKE_TENANT = uuid4()


def _stub_demo(mock_sb):
    """Patch _scoped_business_context to return (mock_sb, fake_tenant)."""
    return patch("chromagora_api.routes.demo._scoped_business_context", return_value=(mock_sb, _FAKE_TENANT))


def _make_mock_sb():
    """Create a mock Supabase client that handles both insert and tenant queries."""
    mock_sb = MagicMock()

    # Insert result — route calls sb.table("events").insert({...}).execute()
    # and expects .data[0]["id"]
    mock_insert_resp = MagicMock()
    mock_insert_resp.data = [{"id": "evt-test"}]
    mock_sb.table.return_value.insert.return_value.execute.return_value = mock_insert_resp

    return mock_sb, mock_insert_resp


class TestDemoReviewRequestSimulation:
    def test_successful(self):
        mock_sb, _ = _make_mock_sb()

        with _stub_demo(mock_sb):
            with patch("chromagora_api.routes.demo.run_review_request", return_value={"status": "completed"}):
                resp = _client.post("/demo/review-request-simulation", json={
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

    def test_no_database(self):
        with patch("chromagora_api.routes.demo.get_supabase", return_value=None):
            resp = _client.post("/demo/review-request-simulation", json={
                "business_id": str(uuid4()),
                "customer_name": "Test",
                "customer_contact": "test@test.com",
                "job_summary": "Test job",
                "completed_at": "2026-06-24T10:00:00Z",
            })
        assert resp.status_code == 503


class TestDemoStaleQuoteSimulation:
    def test_successful(self):
        mock_sb, _ = _make_mock_sb()

        with _stub_demo(mock_sb):
            with patch("chromagora_api.routes.demo.run_stale_quote_followup", return_value={"status": "completed"}):
                resp = _client.post("/demo/stale-quote-simulation", json={
                    "business_id": str(uuid4()),
                    "customer_name": "Test",
                    "customer_contact": "test@test.com",
                    "service_type": "roofing",
                    "quote_sent_at": "2026-06-10T10:00:00Z",
                })

        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


class TestDemoOpportunitySimulation:
    def test_successful(self):
        mock_sb, _ = _make_mock_sb()

        with _stub_demo(mock_sb):
            with patch("chromagora_api.routes.demo.evaluate_opportunity", return_value={"status": "completed", "fit_score": 0.7}):
                resp = _client.post("/demo/opportunity-simulation", json={
                    "business_id": str(uuid4()),
                    "opportunity_type": "rfp",
                    "source_name": "City of Austin",
                    "title": "Roof replacement",
                })

        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
