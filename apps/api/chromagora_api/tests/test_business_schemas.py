"""Tests for business domain schemas."""

from datetime import datetime
from uuid import uuid4

import pytest

from chromagora_schemas.business import (
    BusinessCreate,
    BusinessStatus,
    BusinessServiceCreate,
)
from chromagora_schemas.twin import (
    TwinUpdate,
    TwinResponse,
    CapacityProfileUpdate,
)
from chromagora_schemas.claims import (
    ApprovedClaimCreate,
    ForbiddenClaimCreate,
)


class TestBusinessSchemas:

    def test_business_create(self):
        b = BusinessCreate(
            legal_name="Acme Landscaping Inc.",
            slug="acme-landscaping",
            business_type="landscaping",
        )
        assert b.legal_name == "Acme Landscaping Inc."
        assert b.slug == "acme-landscaping"

    def test_business_create_minimal(self):
        b = BusinessCreate(legal_name="Co", slug="co")
        assert b.business_type is None

    def test_service_create(self):
        s = BusinessServiceCreate(
            name="Lawn Mowing",
            category="maintenance",
            base_price_notes="50",
        )
        assert s.is_active is True
        assert s.name == "Lawn Mowing"

    def test_business_status_enum(self):
        assert BusinessStatus.ACTIVE == "active"
        assert BusinessStatus.ARCHIVED == "archived"


class TestTwinSchemas:

    def test_twin_update(self):
        t = TwinUpdate(summary="Full twin notes")
        assert t.summary == "Full twin notes"

    def test_twin_response(self):
        now = datetime.now()
        r = TwinResponse(
            id=uuid4(),
            business_id=uuid4(),
            version=1,
            status="active",
            created_at=now,
            updated_at=now,
        )
        assert r.version == 1
        assert r.status == "active"

    def test_capacity_update(self):
        c = CapacityProfileUpdate(
            crew_notes="2-person crew",
            max_daily_estimates=5,
        )
        assert c.max_daily_estimates == 5
        assert c.crew_notes == "2-person crew"


class TestClaimSchemas:

    def test_approved_claim(self):
        c = ApprovedClaimCreate(
            claim_type="licensed",
            claim_text="Licensed in Ontario",
            approved_by="operator",
        )
        assert c.is_active is True
        assert c.claim_type == "licensed"

    def test_forbidden_claim(self):
        c = ForbiddenClaimCreate(
            claim_type="emergency",
            claim_text="24/7 emergency available",
            reason="Not verified for emergency response",
        )
        assert c.claim_type == "emergency"
        assert c.reason is not None

    def test_claim_defaults(self):
        c = ForbiddenClaimCreate(
            claim_type="pricing",
            claim_text="Do not guarantee price",
        )
        assert c.is_active is True
        assert c.reason is None
