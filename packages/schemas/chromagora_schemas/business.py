"""Business domain schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class BusinessType(str, Enum):
    LANDSCAPING = "landscaping"
    SNOW_REMOVAL = "snow_removal"
    BOTH = "both"
    OTHER = "other"


class BusinessBase(BaseModel):
    legal_name: str
    public_name: Optional[str] = None
    slug: str
    business_type: Optional[str] = None
    primary_vertical: Optional[str] = None
    country: Optional[str] = None
    province_state: Optional[str] = None
    city: Optional[str] = None
    service_area_description: Optional[str] = None


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    legal_name: Optional[str] = None
    public_name: Optional[str] = None
    business_type: Optional[str] = None
    primary_vertical: Optional[str] = None
    country: Optional[str] = None
    province_state: Optional[str] = None
    city: Optional[str] = None
    service_area_description: Optional[str] = None
    status: Optional[BusinessStatus] = None


class BusinessResponse(BusinessBase):
    id: UUID
    tenant_id: UUID
    status: BusinessStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    base_price_notes: Optional[str] = None
    margin_notes: Optional[str] = None


class BusinessServiceCreate(BusinessServiceBase):
    pass


class BusinessServiceResponse(BusinessServiceBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
