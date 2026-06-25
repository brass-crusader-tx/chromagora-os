"""Tests for CRM integration abstraction (Chapter 22.2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from chromagora_api.services.crm_integration import (
    CrmLead,
    CrmProvider,
    CrmTask,
    InternalCrmLiteProvider,
    get_crm_provider,
)


# ---------------------------------------------------------------------------
# InternalCrmLiteProvider tests
# ---------------------------------------------------------------------------

class TestInternalCrmLiteProvider:

    def test_create_lead(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "business_id": str(uuid4()),
            "customer_name": "Test",
            "customer_contact": "test@example.com",
            "source": "web",
            "status": "new",
        }])
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
            lead_id = provider.create_lead(uuid4(), CrmLead(
                id="",
                customer_name="Test",
                customer_contact="test@example.com",
                source="web",
            ))

        assert lead_id is not None
        mock_sb.table.assert_called_with("leads")

    def test_update_lead(self):
        lead_id = str(uuid4())
        business_id = str(uuid4())
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.execute.side_effect = [
            MagicMock(data=[{
                "id": lead_id,
                "business_id": business_id,
                "customer_name": "John",
                "customer_contact": "555-1234",
                "source": "referral",
                "status": "new",
            }]),
            MagicMock(data=[{"id": lead_id}]),
        ]
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
            result = provider.update_lead(lead_id, {"status": "qualified"})

        assert result is True

    def test_update_lead_not_found(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
            result = provider.update_lead(str(uuid4()), {"status": "qualified"})

        assert result is False

    def test_create_task(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "business_id": str(uuid4()),
            "title": "Follow up",
            "status": "pending",
        }])
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch("chromagora_api.db.base.get_supabase_admin", return_value=mock_sb):
            task = CrmTask(id="", title="Follow up", status="pending")
            task_id = provider.create_task(uuid4(), task)

        assert task_id is not None

    def test_get_lead_found(self):
        lead_id = str(uuid4())
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            "id": lead_id,
            "business_id": str(uuid4()),
            "customer_name": "John",
            "customer_contact": "555-1234",
            "source": "referral",
            "status": "qualified",
        }])
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch.object(provider, "_get_supabase", return_value=mock_sb):
            lead = provider.get_lead(lead_id)

        assert lead is not None
        assert lead.customer_name == "John"

    def test_get_lead_not_found(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch.object(provider, "_get_supabase", return_value=mock_sb):
            lead = provider.get_lead(str(uuid4()))

        assert lead is None

    def test_list_recent_leads(self):
        mock_sb = MagicMock()
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.order.return_value = table_mock
        table_mock.limit.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[
            {"id": str(uuid4()), "customer_name": "A", "customer_contact": "a@b.com", "source": "web", "status": "new"},
            {"id": str(uuid4()), "customer_name": "B", "customer_contact": "b@b.com", "source": "referral", "status": "new"},
        ])
        mock_sb.table.return_value = table_mock

        provider = InternalCrmLiteProvider()
        with patch.object(provider, "_get_supabase", return_value=mock_sb):
            leads = provider.list_recent_leads(uuid4())

        assert len(leads) == 2
        assert leads[0].customer_name == "A"


# ---------------------------------------------------------------------------
# Provider factory tests
# ---------------------------------------------------------------------------

def test_get_crm_provider_default():
    """Default CRM provider is internal."""
    with patch("chromagora_api.services.crm_integration.CRM_PROVIDER", "internal"):
        provider = get_crm_provider()
        assert isinstance(provider, InternalCrmLiteProvider)


def test_get_crm_provider_hubspot_not_implemented():
    """HubSpot provider raises NotImplementedError."""
    with patch("chromagora_api.services.crm_integration.CRM_PROVIDER", "hubspot"):
        with pytest.raises(NotImplementedError):
            get_crm_provider()


# ---------------------------------------------------------------------------
# CrmLead model tests
# ---------------------------------------------------------------------------

def test_crm_lead_to_dict():
    lead = CrmLead(
        id="test-id",
        customer_name="John",
        customer_contact="555-1234",
        source="web",
        status="new",
    )
    d = lead.to_dict()
    assert d["id"] == "test-id"
    assert d["customer_name"] == "John"
