"""Business claims schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ApprovedClaimBase(BaseModel):
    claim_type: str
    claim_text: str
    evidence_json: Optional[dict] = None
    approved_by: Optional[str] = None
    is_active: bool = True


class ApprovedClaimCreate(ApprovedClaimBase):
    pass


class ApprovedClaimResponse(ApprovedClaimBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ForbiddenClaimBase(BaseModel):
    claim_type: str
    claim_text: str
    reason: Optional[str] = None
    is_active: bool = True


class ForbiddenClaimCreate(ForbiddenClaimBase):
    pass


class ForbiddenClaimResponse(ForbiddenClaimBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
