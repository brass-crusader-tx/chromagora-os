"""Tests for autonomy scorecard service and routes (Chapter 25)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from chromagora_api.main import app
from chromagora_api.services.autonomy_scorecard import (
    AutonomyScorecard,
    get_autonomy_scorecard,
    scorecard_to_dict,
    _recommend_autonomy_level,
    _generate_notes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_supabase(proposals=None, executions=None, events=None, envelopes=None):
    """Create mock Supabase client with chainable table operations."""
    mock_sb = MagicMock()

    proposals = proposals or []
    executions = executions or []
    events = events or []
    envelopes = envelopes or []

    table_data = {
        "action_proposals": proposals,
        "action_executions": executions,
        "events": events,
        "authority_envelopes": envelopes,
    }

    def make_table(name):
        t = MagicMock()
        t.select.return_value = t
        t.eq.return_value = t
        t.execute.return_value = MagicMock(data=table_data.get(name, []))
        return t

    mock_sb.table.side_effect = make_table
    return mock_sb


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

def test_get_autonomy_scorecard_empty():
    """Scorecard with no data returns baseline values."""
    mock_sb = _mock_supabase()

    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=mock_sb):
        sc = get_autonomy_scorecard(uuid4())

    assert sc.total_proposals == 0
    assert sc.avg_confidence == 0.0
    assert sc.autonomy_level_recommended == 1


def test_get_autonomy_scorecard_with_proposals():
    """Scorecard counts proposals correctly."""
    proposals = [
        {"id": str(uuid4()), "status": "approval_required", "confidence": 0.6, "risk_level": "low"},
        {"id": str(uuid4()), "status": "approved", "confidence": 0.8, "risk_level": "low"},
        {"id": str(uuid4()), "status": "blocked", "confidence": 0.3, "risk_level": "high"},
    ]
    mock_sb = _mock_supabase(proposals=proposals)

    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=mock_sb):
        sc = get_autonomy_scorecard(uuid4())

    assert sc.total_proposals == 3
    assert sc.approvals_required == 1
    assert sc.approvals_accepted == 1
    assert sc.blocked_by_policy == 1
    assert sc.avg_confidence == pytest.approx(0.567, abs=0.01)


def test_get_autonomy_scorecard_with_violations():
    """Scorecard counts policy violations."""
    events = [{"id": str(uuid4())}]
    mock_sb = _mock_supabase(events=events)

    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=mock_sb):
        sc = get_autonomy_scorecard(uuid4())

    assert sc.violations == 1


def test_get_autonomy_scorecard_with_executions():
    """Scorecard counts executions by type."""
    executions = [
        {"id": str(uuid4()), "result_status": "dry_run", "reversibility": "reversible"},
        {"id": str(uuid4()), "result_status": "success", "reversibility": "reversible"},
        {"id": str(uuid4()), "result_status": "success", "reversibility": "irreversible"},
        {"id": str(uuid4()), "result_status": "failed", "reversibility": "reversible"},
    ]
    mock_sb = _mock_supabase(executions=executions)

    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=mock_sb):
        sc = get_autonomy_scorecard(uuid4())

    assert sc.dry_run_executions == 1
    assert sc.real_executions == 2
    assert sc.failures == 1


def test_get_autonomy_scorecard_no_supabase():
    """Scorecard handles no Supabase gracefully."""
    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=None):
        sc = get_autonomy_scorecard(uuid4())

    assert "Database not available" in sc.notes[0]


def test_get_autonomy_scorecard_with_envelopes():
    """Scorecard reads current autonomy level from envelopes."""
    envelopes = [
        {"autonomy_level": 2},
        {"autonomy_level": 3},
    ]
    mock_sb = _mock_supabase(envelopes=envelopes)

    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=mock_sb):
        sc = get_autonomy_scorecard(uuid4())

    assert sc.autonomy_level_current == 3


# ---------------------------------------------------------------------------
# Recommendation tests (pure unit tests — no Supabase needed)
# ---------------------------------------------------------------------------

def test_recommend_level_1_baseline():
    """Low proposal count stays at level 1."""
    sc = AutonomyScorecard(business_id=str(uuid4()), total_proposals=5)
    assert _recommend_autonomy_level(sc) == 1


def test_recommend_level_2_qualified():
    """Meets level 2 criteria."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        total_proposals=25,
        avg_confidence=0.75,
        escalation_rate=0.05,
        violations=0,
    )
    assert _recommend_autonomy_level(sc) == 2


def test_recommend_level_3_qualified():
    """Meets level 3 criteria."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        total_proposals=60,
        avg_confidence=0.85,
        escalation_rate=0.03,
        violations=0,
        real_executions=15,
    )
    assert _recommend_autonomy_level(sc) == 3


def test_recommend_level_4_qualified():
    """Meets level 4 criteria."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        total_proposals=120,
        avg_confidence=0.9,
        escalation_rate=0.01,
        violations=0,
        real_executions=30,
    )
    assert _recommend_autonomy_level(sc) == 4


def test_recommend_never_below_1():
    """Recommendation never goes below level 1."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        total_proposals=0,
        violations=5,
    )
    assert _recommend_autonomy_level(sc) >= 1


def test_recommend_violations_decrease():
    """Violations decrease recommended level."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        total_proposals=25,
        avg_confidence=0.75,
        escalation_rate=0.05,
        violations=2,
        autonomy_level_current=3,
    )
    rec = _recommend_autonomy_level(sc)
    assert rec < 3 or rec == 1


# ---------------------------------------------------------------------------
# Notes generation
# ---------------------------------------------------------------------------

def test_notes_with_violations():
    """Notes include violation warning."""
    sc = AutonomyScorecard(business_id=str(uuid4()), violations=3)
    notes = _generate_notes(sc)
    assert any("violation" in n.lower() for n in notes)


def test_notes_with_high_escalation():
    """Notes flag high escalation rate."""
    sc = AutonomyScorecard(business_id=str(uuid4()), total_proposals=10, approvals_required=5)
    sc.escalation_rate = 0.5
    notes = _generate_notes(sc)
    assert any("escalation" in n.lower() for n in notes)


def test_notes_recommend_increase():
    """Notes suggest increase when appropriate."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        autonomy_level_current=1,
        autonomy_level_recommended=3,
    )
    notes = _generate_notes(sc)
    assert any("increase" in n.lower() for n in notes)


# ---------------------------------------------------------------------------
# Dict serialization
# ---------------------------------------------------------------------------

def test_scorecard_to_dict():
    """scorecard_to_dict returns all expected keys."""
    sc = AutonomyScorecard(
        business_id=str(uuid4()),
        total_proposals=10,
        autonomy_level_current=2,
        autonomy_level_recommended=3,
    )
    d = scorecard_to_dict(sc)

    assert "business_id" in d
    assert "total_proposals" in d
    assert "autonomy_level_current" in d
    assert "autonomy_level_recommended" in d
    assert "notes" in d
    assert isinstance(d["notes"], list)


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_get_scorecard_route(transport):
    """GET /businesses/{id}/autonomy/scorecard returns scorecard."""
    mock_sb = _mock_supabase()

    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/businesses/{uuid4()}/autonomy/scorecard"
            )

    assert response.status_code == 200
    data = response.json()
    assert "business_id" in data
    assert "total_proposals" in data
    assert "autonomy_level_current" in data
    assert "autonomy_level_recommended" in data
    assert "notes" in data


@pytest.mark.asyncio
async def test_get_scorecard_no_supabase(transport):
    """Scorecard route handles missing Supabase gracefully."""
    with patch("chromagora_api.services.autonomy_scorecard.get_supabase", return_value=None):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/businesses/{uuid4()}/autonomy/scorecard"
            )

    assert response.status_code == 200
