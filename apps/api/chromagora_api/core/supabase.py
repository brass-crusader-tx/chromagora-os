"""Supabase client initialization."""

import logging
from supabase import Client, create_client

from chromagora_api.core.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None
_supabase_admin_client: Client | None = None


def get_supabase() -> Client | None:
    """Get the anon Supabase client (RLS enforced)."""
    global _supabase_client
    if _supabase_client is None and settings.supabase_url and settings.supabase_anon_key:
        try:
            _supabase_client = create_client(
                settings.supabase_url, settings.supabase_anon_key
            )
            logger.info("Supabase anon client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase anon client: {e}")
    return _supabase_client


def get_supabase_admin() -> Client | None:
    """Get the service-role Supabase client (bypasses RLS)."""
    global _supabase_admin_client
    if _supabase_admin_client is None and settings.supabase_url and settings.supabase_service_role_key:
        try:
            _supabase_admin_client = create_client(
                settings.supabase_url, settings.supabase_service_role_key
            )
            logger.info("Supabase admin client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase admin client: {e}")
    return _supabase_admin_client


def is_supabase_configured() -> bool:
    """Check if Supabase credentials are available."""
    return bool(settings.supabase_url and settings.supabase_anon_key)
