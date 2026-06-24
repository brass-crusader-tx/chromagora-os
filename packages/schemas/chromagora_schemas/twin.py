"""Business Twin schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TwinBase(BaseModel):
    summary: Optional[str] = None


class TwinUpdate(BaseModel):
    summary: Optional[str] = None


class TwinResponse(BaseModel):
    id: UUID
    business_id: UUID
    version: int
    status: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CapacityProfileBase(BaseModel):
    crew_notes: Optional[str] = None
    equipment_notes: Optional[str] = None
    scheduling_notes: Optional[str] = None
    max_daily_estimates: Optional[int] = None
    max_weekly_jobs: Optional[int] = None
    seasonal_constraints: Optional[str] = None


class CapacityProfileUpdate(BaseModel):
    crew_notes: Optional[str] = None
    equipment_notes: Optional[str] = None
    scheduling_notes: Optional[str] = None
    max_daily_estimates: Optional[int] = None
    max_weekly_jobs: Optional[int] = None
    seasonal_constraints: Optional[str] = None


class CapacityProfileResponse(CapacityProfileBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
