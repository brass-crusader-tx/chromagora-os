"""Health check and version routes."""

from fastapi import APIRouter

from chromagora_api.core.config import settings
from chromagora_api.core.supabase import is_supabase_configured

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Health check endpoint. Reports Supabase connection availability."""
    return {
        "status": "ok",
        "version": settings.version,
        "environment": settings.chromagora_env,
        "supabase_configured": is_supabase_configured(),
    }


@router.get("/version")
async def version():
    """API version endpoint."""
    return {
        "version": settings.version,
        "environment": settings.chromagora_env,
    }
