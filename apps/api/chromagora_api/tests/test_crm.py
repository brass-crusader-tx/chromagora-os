"""Tests for CRM-lite schemas and service logic."""

import pytest
from uuid import uuid4

from chromagora_schemas.crm import (
    LeadCreate, LeadUpdate, LeadResponse,
    QuoteCreate, QuoteUpdate,
    JobCreate, JobUpdate,
    MessageDraftCreate, MessageDraftUpdate,
)


class TestLeadSchema:
    def test_create(self):
        lead = LeadCreate(
            business_id=uuid4(),
            customer_name="John Doe",
            customer_contact="john@example.com",
        )
        assert lead.status == "new"
        assert lead.source is None

    def test_update_partial(self):
        update = LeadUpdate(status="qualified")
        data = update.model_dump(mode="json")
        assert data["status"] == "qualified"
        assert data.get("customer_name") is None

    def test_create_with_source(self):
        lead = LeadCreate(
            business_id=uuid4(),
            customer_name="Jane",
            customer_contact="555-1234",
            source="website",
            service_type="plumbing",
        )
        assert lead.source == "website"
        assert lead.service_type == "plumbing"


class TestQuoteSchema:
    def test_create(self):
        quote = QuoteCreate(
            business_id=uuid4(),
            service_type="roofing",
        )
        assert quote.status == "draft"
        assert quote.quote_amount is None

    def test_create_with_amount(self):
        quote = QuoteCreate(
            business_id=uuid4(),
            service_type="roofing",
            quote_amount=5000.00,
        )
        assert quote.quote_amount == 5000.00


class TestJobSchema:
    def test_create(self):
        job = JobCreate(
            business_id=uuid4(),
            customer_name="Bob",
            service_type="electrical",
        )
        assert job.status == "scheduled"
        assert job.lead_id is None
        assert job.quote_id is None


class TestMessageDraftSchema:
    def test_create_email(self):
        draft = MessageDraftCreate(
            business_id=uuid4(),
            channel="email",
            recipient="customer@example.com",
            subject="Quote follow-up",
            body="Hi, following up on our quote...",
        )
        assert draft.channel == "email"
        assert draft.status == "draft"

    def test_create_sms(self):
        draft = MessageDraftCreate(
            business_id=uuid4(),
            channel="sms",
            recipient="+15551234567",
            body="Your job is scheduled for tomorrow.",
        )
        assert draft.channel == "sms"

    def test_update_status(self):
        update = MessageDraftUpdate(status="approved")
        data = update.model_dump(mode="json")
        assert data["status"] == "approved"
