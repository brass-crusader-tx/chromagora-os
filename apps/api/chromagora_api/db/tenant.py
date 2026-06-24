"""Tenant context management.

In production, tenant context is set via Supabase RLS policies
using current_setting('app.current_tenant', true).

This module provides helpers for setting the tenant context
in the Supabase PostgREST session.
"""

from supabase import Client


def set_tenant_context(client: Client, tenant_id: str) -> None:
    """Set the current tenant context for RLS.

    This calls a database function that does:
    SET LOCAL app.current_tenant = tenant_id;
    """
    client.rpc("set_tenant_context", {"tenant_id": tenant_id}).execute()
