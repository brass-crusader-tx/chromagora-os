"""Tests for mobile readiness endpoints (Chapter 19)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from chromagora_api.main import app
from chromagora_api.services import mobile_service


@pytest.fixture
def transport():
    return ASGITransport(app=app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_supabase_table(data=None, insert_data=None):
    """Create a mock Supabase client with chainable table operations."""
    mock_sb = MagicMock()

    table_mock = MagicMock()
    if data is not None:
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.in_.return_value = table_mock
        table_mock.order.return_value = table_mock
        table_mock.limit.return_value = table_mock
        table_mock.gte.return_value = table_mock
        table_mock.lte.return_value = table_mock
        table_mock.lt.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=data)
    elif insert_data is not None:
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=insert_data)

    mock_sb.table.return_value = table_mock
    return mock_sb, table_mock


# ---------------------------------------------------------------------------
# GET /mobile/today
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_today_returns_dashboard_structure():
    """GET /mobile/today returns all expected dashboard keys."""
    mock_sb, _ = _mock_supabase_table(data=[])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/mobile/today?business_id=12345678-1234-5678-1234-567812345678")

    assert response.status_code == 200
    data = response.json()
    assert "business_id" in data
    assert "generated_at" in data
    assert "urgent_approvals" in data
    assert "recent_events" in data
    assert "active_workflows" in data
    assert "upcoming_jobs" in data
    assert "upcoming_opportunities" in data
    assert "blocked_agents" in data


@pytest.mark.asyncio
async def test_mobile_today_no_supabase_returns_503():
    """GET /mobile/today returns 503 when Supabase is not configured."""
    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/mobile/today?business_id=12345678-1234-5678-1234-567812345678")

    assert response.status_code == 503


# ---------------------------------------------------------------------------
# GET /mobile/approvals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_approvals_list_returns_list():
    """GET /mobile/approvals returns a list."""
    mock_sb, _ = _mock_supabase_table(data=[])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/mobile/approvals?business_id=12345678-1234-5678-1234-567812345678")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_mobile_approvals_list_with_data():
    """GET /mobile/approvals enriches with action proposal data."""
    approval = {
        "id": "a1234567-1234-5678-1234-567812345678",
        "action_proposal_id": "p1234567-1234-5678-1234-567812345678",
        "status": "pending",
        "requested_at": "2026-06-24T10:00:00Z",
        "decided_at": None,
        "decision_notes": None,
        "expires_at": None,
        "requested_by_type": "agent",
    }
    proposal = {
        "id": "p1234567-1234-5678-1234-567812345678",
        "title": "Send review request",
        "description": "Request review from customer",
        "action_type": "reputation.queue_review_request",
        "risk_level": "low",
    }

    mock_sb = MagicMock()

    # First call: approval_requests table
    approvals_table = MagicMock()
    approvals_table.select.return_value = approvals_table
    approvals_table.eq.return_value = approvals_table
    approvals_table.order.return_value = approvals_table
    approvals_table.limit.return_value = approvals_table
    approvals_table.execute.return_value = MagicMock(data=[approval])

    # Second call: action_proposals table (for enrichment)
    proposals_table = MagicMock()
    proposals_table.select.return_value = proposals_table
    proposals_table.eq.return_value = proposals_table
    proposals_table.execute.return_value = MagicMock(data=[proposal])

    def table_router(name):
        if name == "approval_requests":
            return approvals_table
        if name == "action_proposals":
            return proposals_table
        return MagicMock()

    mock_sb.table.side_effect = table_router

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/mobile/approvals?business_id=12345678-1234-5678-1234-567812345678")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["action_proposal"]["title"] == "Send review request"


# ---------------------------------------------------------------------------
# POST /mobile/approvals/{id}/approve
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_approve_updates_status():
    """POST /mobile/approvals/{id}/approve sets status to approved."""
    updated = {
        "id": "a1234567-1234-5678-1234-567812345678",
        "status": "approved",
        "decided_by": "operator",
        "decided_at": "2026-06-24T18:00:00Z",
    }
    mock_sb, table_mock = _mock_supabase_table(data=updated)

    # Make update chain return the updated row
    table_mock.update.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[updated])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/mobile/approvals/a1234567-1234-5678-1234-567812345678/approve")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_mobile_approve_not_found_returns_404():
    """POST /mobile/approvals/{id}/approve returns 404 for unknown ID."""
    mock_sb, table_mock = _mock_supabase_table(data=[])
    table_mock.update.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/mobile/approvals/a1234567-1234-5678-1234-567812345678/approve")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /mobile/approvals/{id}/reject
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_reject_updates_status():
    """POST /mobile/approvals/{id}/reject sets status to rejected."""
    updated = {
        "id": "a1234567-1234-5678-1234-567812345678",
        "status": "rejected",
        "decided_by": "operator",
        "decided_at": "2026-06-24T18:00:00Z",
        "decision_notes": "Not ready yet",
    }
    mock_sb, table_mock = _mock_supabase_table(data=updated)
    table_mock.update.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[updated])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mobile/approvals/a1234567-1234-5678-1234-567812345678/reject?notes=Not%20ready%20yet"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["decision_notes"] == "Not ready yet"


# ---------------------------------------------------------------------------
# GET /mobile/command-feed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_command_feed_returns_list():
    """GET /mobile/command-feed returns a list of events."""
    mock_sb, _ = _mock_supabase_table(data=[])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/mobile/command-feed?business_id=12345678-1234-5678-1234-567812345678")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# GET /mobile/jobs/today
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_jobs_today_returns_list():
    """GET /mobile/jobs/today returns a list."""
    mock_sb, _ = _mock_supabase_table(data=[])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/mobile/jobs/today?business_id=12345678-1234-5678-1234-567812345678")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# POST /mobile/capture/note
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_capture_note_creates_event():
    """POST /mobile/capture/note creates an event record."""
    inserted = {
        "id": "e1234567-1234-5678-1234-567812345678",
        "business_id": "b1234567-1234-5678-1234-567812345678",
        "event_type": "mobile.note_captured",
        "payload_json": {"content": "Customer requested callback", "note_type": "field_note"},
        "occurred_at": "2026-06-24T18:00:00Z",
        "created_at": "2026-06-24T18:00:00Z",
    }
    mock_sb, table_mock = _mock_supabase_table(insert_data=[inserted])
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[inserted])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mobile/capture/note",
                json={
                    "business_id": "b1234567-1234-5678-1234-567812345678",
                    "content": "Customer requested callback",
                    "note_type": "field_note",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "mobile.note_captured"


# ---------------------------------------------------------------------------
# POST /mobile/capture/photo-metadata
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mobile_capture_photo_creates_event():
    """POST /mobile/capture/photo-metadata creates an event record."""
    inserted = {
        "id": "e1234567-1234-5678-1234-567812345678",
        "business_id": "b1234567-1234-5678-1234-567812345678",
        "event_type": "mobile.photo_captured",
        "payload_json": {"photo_url": "https://example.com/photo.jpg", "caption": "Before photo"},
        "occurred_at": "2026-06-24T18:00:00Z",
        "created_at": "2026-06-24T18:00:00Z",
    }
    mock_sb, table_mock = _mock_supabase_table(insert_data=[inserted])
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[inserted])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mobile/capture/photo-metadata",
                json={
                    "business_id": "b1234567-1234-5678-1234-567812345678",
                    "photo_url": "https://example.com/photo.jpg",
                    "caption": "Before photo",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "mobile.photo_captured"


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

def test_get_mobile_today_returns_dict_structure():
    """Service: get_mobile_today returns expected keys even with empty data."""
    mock_sb, _ = _mock_supabase_table(data=[])

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb):
        from uuid import uuid4
        result = mobile_service.get_mobile_today(uuid4())

    assert isinstance(result, dict)
    assert "business_id" in result
    assert "urgent_approvals" in result
    assert "recent_events" in result
    assert "active_workflows" in result
    assert "upcoming_jobs" in result
    assert "upcoming_opportunities" in result
    assert "blocked_agents" in result


def test_capture_note_service():
    """Service: capture_note inserts into events table."""
    inserted = {"id": "test-id", "event_type": "mobile.note_captured"}
    mock_sb = MagicMock()
    table_mock = MagicMock()
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[inserted])
    mock_sb.table.return_value = table_mock

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        from uuid import uuid4
        result = mobile_service.capture_note(uuid4(), "Test note")

    assert result["event_type"] == "mobile.note_captured"
    mock_sb.table.assert_called_with("events")


def test_capture_photo_metadata_service():
    """Service: capture_photo_metadata inserts into events table."""
    inserted = {"id": "test-id", "event_type": "mobile.photo_captured"}
    mock_sb = MagicMock()
    table_mock = MagicMock()
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[inserted])
    mock_sb.table.return_value = table_mock

    with patch("chromagora_api.services.mobile_service.get_supabase", return_value=mock_sb), \
         patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
        from uuid import uuid4
        result = mobile_service.capture_photo_metadata(uuid4(), photo_url="https://example.com/1.jpg")

    assert result["event_type"] == "mobile.photo_captured"
    mock_sb.table.assert_called_with("events")
