"""Shared test fixtures for mocked single-tenant API behavior."""

from __future__ import annotations

import importlib

import pytest


TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"
TEST_BUSINESS_ID = "12345678-1234-5678-1234-567812345678"


def _active_tenant_id(*_args, **_kwargs) -> str:
    return TEST_TENANT_ID


def _active_business_ids(*_args, **_kwargs) -> list[str]:
    return [TEST_BUSINESS_ID]


def _business_tenant_id(*_args, **_kwargs) -> str:
    return TEST_TENANT_ID


@pytest.fixture(autouse=True)
def mocked_tenant_scope(monkeypatch):
    """Keep legacy Supabase mocks focused on behavior, not tenant plumbing."""

    import chromagora_api.db.base as db_base
    import chromagora_api.db.tenant as tenant

    monkeypatch.setattr(tenant, "get_active_tenant_id", _active_tenant_id)
    monkeypatch.setattr(tenant, "get_active_business_ids", _active_business_ids)
    monkeypatch.setattr(tenant, "get_business_tenant_id", _business_tenant_id)
    monkeypatch.setattr(tenant, "require_business_tenant_id", _business_tenant_id)
    monkeypatch.setattr(db_base, "get_supabase_admin", lambda: db_base.get_supabase())

    scoped_modules = [
        "chromagora_api.routes.agent_tasks",
        "chromagora_api.routes.agents",
        "chromagora_api.routes.approvals",
        "chromagora_api.routes.authority",
        "chromagora_api.routes.businesses",
        "chromagora_api.routes.crm",
        "chromagora_api.routes.demo",
        "chromagora_api.routes.ledger",
        "chromagora_api.routes.memory",
        "chromagora_api.routes.opportunities",
        "chromagora_api.routes.procurement",
        "chromagora_api.routes.tools",
        "chromagora_api.routes.voice",
        "chromagora_api.routes.workflows",
        "chromagora_api.services.autonomy_scorecard",
        "chromagora_api.services.mobile_service",
    ]

    for module_name in scoped_modules:
        module = importlib.import_module(module_name)
        if hasattr(module, "get_active_tenant_id"):
            monkeypatch.setattr(module, "get_active_tenant_id", _active_tenant_id)
        if hasattr(module, "get_active_business_ids"):
            monkeypatch.setattr(module, "get_active_business_ids", _active_business_ids)
        if hasattr(module, "get_business_tenant_id"):
            monkeypatch.setattr(module, "get_business_tenant_id", _business_tenant_id)
