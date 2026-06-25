"""API key authentication middleware."""

from __future__ import annotations

import secrets

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from chromagora_api.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Build valid keys from config
VALID_API_KEYS: set[str] = set()
if settings.api_keys:
    VALID_API_KEYS.update(k.strip() for k in settings.api_keys.split(",") if k.strip())


def _validate_key(api_key: str | None) -> bool:
    """Validate an API key against configured keys."""
    if not api_key:
        return False
    if settings.chromagora_env == "development" and not settings.enforce_auth:
        return True
    if not VALID_API_KEYS:
        return False
    # Constant-time comparison to avoid timing attacks
    for valid_key in VALID_API_KEYS:
        if secrets.compare_digest(api_key, valid_key):
            return True
    return False


def apply_auth(app: FastAPI) -> None:
    """Add API key protection to all non-health routes via middleware."""
    protected_prefixes = [
        "/businesses", "/agents", "/approvals", "/workflows",
        "/opportunities", "/ledger", "/memory", "/voice",
        "/crm", "/tools", "/authority", "/autonomy", "/demo",
        "/mobile", "/procurement", "/agent-tasks",
    ]

    @app.middleware("http")
    async def _api_key_middleware(request: Request, call_next):
        path = request.url.path

        # Skip auth for health, docs, openapi
        if path in ("/health", "/docs", "/openapi.json", "/favicon.ico"):
            return await call_next(request)

        # Skip auth in dev mode unless enforced
        if settings.chromagora_env == "development" and not settings.enforce_auth:
            return await call_next(request)

        # Skip CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if path needs protection
        needs_auth = any(path.startswith(p) for p in protected_prefixes)
        if not needs_auth:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not _validate_key(api_key):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid X-API-Key header"},
            )

        return await call_next(request)
