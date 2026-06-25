"""Tests for voice service and routes (Chapter 23)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from chromagora_api.main import app
from chromagora_schemas.voice import (
    CallRecordCreate,
    CallSummaryCreate,
    VoiceQualificationResult,
)
from chromagora_api.services import voice_service


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestVoiceService:

    def test_create_call_record(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "business_id": str(uuid4()),
            "caller_phone": "+15551234567",
            "call_status": "inbound",
            "started_at": "2026-06-24T10:00:00Z",
            "consent_recorded": False,
        }])
        mock_sb.table.return_value = table_mock

        with patch.object(voice_service, "_get_supabase", return_value=mock_sb):
            data = CallRecordCreate(
                business_id=uuid4(),
                caller_phone="+15551234567",
                call_status="inbound",
                started_at=datetime.now(timezone.utc),
            )
            result = voice_service.create_call_record(data.business_id, data)

        assert result is not None
        assert result.caller_phone == "+15551234567"
        mock_sb.table.assert_called_with("call_records")

    def test_get_call_record_not_found(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value = table_mock

        with patch.object(voice_service, "_get_supabase", return_value=mock_sb):
            result = voice_service.get_call_record(uuid4())

        assert result is None

    def test_create_call_summary(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "call_record_id": str(uuid4()),
            "intent": "estimate_request",
            "urgency": "normal",
            "escalation_required": False,
            "confidence": 0.8,
        }])
        mock_sb.table.return_value = table_mock

        with patch.object(voice_service, "_get_supabase", return_value=mock_sb):
            data = CallSummaryCreate(
                call_record_id=uuid4(),
                intent="estimate_request",
                urgency="normal",
                lead_quality="warm",
                escalation_required=False,
                confidence=0.8,
            )
            result = voice_service.create_call_summary(data)

        assert result is not None
        assert result.intent == "estimate_request"

    def test_qualify_call_estimate_request(self):
        result = voice_service.qualify_call_transcript(
            "Hi, I need a quote for lawn mowing. Can you come Tuesday?"
        )
        assert result.caller_intent == "estimate_request"
        assert result.service_type == "lawn_care"
        assert result.estimate_booking_recommended is True

    def test_qualify_call_emergency(self):
        result = voice_service.qualify_call_transcript(
            "EMERGENCY! There's water flooding my basement right now!"
        )
        assert result.caller_intent == "emergency"
        assert result.escalation_required is True
        assert result.urgency == "high"

    def test_qualify_call_booking(self):
        result = voice_service.qualify_call_transcript(
            "I'd like to schedule an appointment for Gutter cleaning"
        )
        assert result.caller_intent == "booking"
        assert result.service_type == "gutter_cleaning"

    def test_qualify_call_photos(self):
        result = voice_service.qualify_call_transcript(
            "Can you send me a photo of the damage?"
        )
        assert result.photos_requested is True

    def test_qualify_call_missing_info(self):
        result = voice_service.qualify_call_transcript("Hi, I need something fixed")
        assert len(result.missing_information) > 0

    def test_qualify_call_low_confidence_no_service(self):
        result = voice_service.qualify_call_transcript("Hello, just calling about stuff")
        assert result.confidence == 0.2
        assert result.next_action == "send_information_packet"


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_create_call_route(transport):
    """POST /voice/calls creates a call record."""
    mock_sb = MagicMock()
    table_mock = MagicMock()
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[{
        "id": str(uuid4()),
        "business_id": "b1234567-1234-5678-1234-567812345678",
        "caller_phone": "+15551234567",
        "call_status": "inbound",
        "started_at": "2026-06-24T10:00:00Z",
        "ended_at": None,
        "recording_url": None,
        "transcript_text": None,
        "consent_recorded": False,
        "trace_id": None,
        "created_at": "2026-06-24T10:00:00Z",
        "updated_at": "2026-06-24T10:00:00Z",
    }])
    mock_sb.table.return_value = table_mock

    with patch("chromagora_api.db.base.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/voice/calls", json={
                "business_id": "b1234567-1234-5678-1234-567812345678",
                "caller_phone": "+15551234567",
                "call_status": "inbound",
                "started_at": "2026-06-24T10:00:00Z",
                "consent_recorded": False,
            })

    assert response.status_code == 201
    data = response.json()
    assert data["call_status"] == "inbound"


@pytest.mark.asyncio
async def test_qualify_route(transport):
    """POST /voice/qualify returns qualification result."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/voice/qualify",
            params={"transcript_text": "I need a snow removal estimate for tomorrow"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "caller_intent" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_get_summary_not_found(transport):
    """GET /voice/calls/{id}/summary returns 404 when not found."""
    mock_sb = MagicMock()
    table_mock = MagicMock()
    table_mock.select.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[])
    mock_sb.table.return_value = table_mock

    with patch("chromagora_api.db.base.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/voice/calls/{uuid4()}/summary"
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_summary_route(transport):
    """POST /voice/summaries creates a call summary."""
    mock_sb = MagicMock()
    table_mock = MagicMock()
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[{
        "id": str(uuid4()),
        "call_record_id": "c1234567-1234-5678-1234-567812345678",
        "intent": "estimate_request",
        "service_type": "lawn_care",
        "urgency": "normal",
        "lead_quality": "warm",
        "escalation_required": False,
        "structured_notes": {},
        "confidence": 0.7,
        "created_at": "2026-06-24T10:00:00Z",
    }])
    mock_sb.table.return_value = table_mock

    with patch("chromagora_api.db.base.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/voice/summaries", json={
                "call_record_id": "c1234567-1234-5678-1234-567812345678",
                "intent": "estimate_request",
                "service_type": "lawn_care",
                "urgency": "normal",
                "lead_quality": "warm",
                "escalation_required": False,
                "confidence": 0.7,
            })

    assert response.status_code == 201
    data = response.json()
    assert data["intent"] == "estimate_request"
