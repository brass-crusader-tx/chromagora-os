"""Tenant context and server-side Supabase helpers."""

import logging

from supabase import Client

from chromagora_api.core.config import settings


class TenantError(Exception):
    """Raised when a business or tenant cannot be resolved (maps to 404)."""
    pass


class DatabaseUnavailable(Exception):
    """Raised when Supabase client is not configured (maps to 503)."""
    pass

logger = logging.getLogger(__name__)


def set_tenant_context(client: Client, tenant_id: str) -> None:
    """Set the current tenant context for RLS.

    This calls a database function that does:
    SET LOCAL app.current_tenant = tenant_id;
    """
    client.rpc("set_tenant_context", {"tenant_id": tenant_id}).execute()


def get_backend_supabase() -> Client:
    """Return the server-only Supabase client used by FastAPI.

    The service-role key must never leave the backend. Because service role
    bypasses RLS, every caller still has to apply tenant or business scoping.
    """
    from chromagora_api.db.base import get_supabase_admin

    sb = get_supabase_admin()
    if not sb:
        raise DatabaseUnavailable("Database not configured")
    return sb


def get_active_tenant_id(client: Client | None = None) -> str:
    """Resolve the tenant this single-tenant API instance should serve."""
    if settings.chromagora_tenant_id:
        return settings.chromagora_tenant_id

    sb = client or get_backend_supabase()
    resp = sb.table("tenants").select("id").order("created_at").limit(2).execute()
    tenants = resp.data or []
    if not tenants:
        raise TenantError("No tenant configured")
    if len(tenants) > 1:
        logger.warning(
            "CHROMAGORA_TENANT_ID is unset; using first tenant from %d tenants",
            len(tenants),
        )
    return tenants[0]["id"]


def get_active_business_ids(client: Client | None = None) -> list[str]:
    """Return business IDs owned by the active tenant."""
    sb = client or get_backend_supabase()
    tenant_id = get_active_tenant_id(sb)
    resp = sb.table("businesses").select("id").eq("tenant_id", tenant_id).execute()
    return [row["id"] for row in (resp.data or [])]


def get_business_tenant_id(business_id: str, client: Client | None = None) -> str | None:
    """Return the active tenant ID when a business belongs to it."""
    sb = client or get_backend_supabase()
    tenant_id = get_active_tenant_id(sb)
    resp = (
        sb.table("businesses")
        .select("tenant_id")
        .eq("id", business_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    if not resp.data:
        return None
    return resp.data[0]["tenant_id"]


def require_business_tenant_id(business_id: str, client: Client | None = None) -> str:
    """Return tenant ID for an active-tenant business or raise RuntimeError."""
    tenant_id = get_business_tenant_id(business_id, client)
    if not tenant_id:
        raise RuntimeError("Business not found")
    return tenant_id
