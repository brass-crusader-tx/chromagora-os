"""Tests for quote follow-up runtime routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from chromagora_api.db.tenant import DatabaseUnavailable
from chromagora_api.main import app


client = TestClient(app)


def test_detect_stale_quotes_returns_results():
    business_id = uuid4()
    tenant_id = uuid4()
    results = [{"quote_id": str(uuid4()), "event_id": str(uuid4())}]

    with (
        patch("chromagora_api.routes.quote_follow_up.get_backend_supabase", return_value=MagicMock()),
        patch("chromagora_api.routes.quote_follow_up.get_business_tenant_id", return_value=str(tenant_id)),
        patch("chromagora_api.routes.quote_follow_up.detect_stale_quotes", return_value=results) as detect,
    ):
        response = client.post(f"/businesses/{business_id}/quotes/detect-stale")

    assert response.status_code == 200
    assert response.json() == {"detected": 1, "results": results}
    detect.assert_called_once_with(business_id=business_id, tenant_id=tenant_id)


def test_detect_stale_quotes_returns_404_when_business_missing():
    business_id = uuid4()

    with (
        patch("chromagora_api.routes.quote_follow_up.get_backend_supabase", return_value=MagicMock()),
        patch("chromagora_api.routes.quote_follow_up.get_business_tenant_id", return_value=None),
    ):
        response = client.post(f"/businesses/{business_id}/quotes/detect-stale")

    assert response.status_code == 404
    assert response.json()["detail"] == "Business not found"


def test_process_events_checks_database_and_dispatches():
    results = [{"event_id": str(uuid4()), "status": "processed"}]

    with (
        patch("chromagora_api.routes.quote_follow_up.get_backend_supabase", return_value=MagicMock()) as get_db,
        patch("chromagora_api.routes.quote_follow_up.process_pending_events", return_value=results) as process,
    ):
        response = client.post("/events/process?event_type=quote.stale&limit=5")

    assert response.status_code == 200
    assert response.json() == {"processed": 1, "results": results}
    get_db.assert_called_once_with()
    process.assert_called_once_with(event_type="quote.stale", limit=5)


def test_process_events_returns_503_when_database_unavailable():
    with patch(
        "chromagora_api.routes.quote_follow_up.get_backend_supabase",
        side_effect=DatabaseUnavailable("Supabase not configured"),
    ):
        response = client.post("/events/process")

    assert response.status_code == 503
    assert response.json()["detail"] == "Supabase not configured"


def test_process_single_event_returns_404_when_missing():
    event_id = uuid4()

    with patch("chromagora_api.routes.quote_follow_up.process_single_event", return_value=None):
        response = client.post(f"/events/{event_id}/process")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"
