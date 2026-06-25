"""Autonomy scorecard routes.

Chapter 25 — Autonomy Increase.
Tracks per-business metrics about proposals, approvals, executions.
Provides operator-facing scorecard for autonomy decisions.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chromagora_api.services.autonomy_scorecard import (
    get_autonomy_scorecard,
    scorecard_to_dict,
)

router = APIRouter(prefix="/businesses/{business_id}/autonomy", tags=["autonomy"])


@router.get("/scorecard")
async def get_scorecard(business_id: UUID):
    """Get the autonomy scorecard for a business.

    Returns metrics about proposals, approvals, executions,
    violations, and recommended autonomy level.
    """
    try:
        scorecard = get_autonomy_scorecard(business_id)
        return scorecard_to_dict(scorecard)
    except RuntimeError as e:
        if str(e) == "Business not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=503, detail=str(e))
