"""Simple in-memory rate limiter middleware."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from chromagora_api.core.config import settings

# Per-IP request timestamps
_requests: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def apply_rate_limit(app: FastAPI) -> None:
    """Add rate limiting middleware (per-IP, sliding window)."""
    rate = settings.rate_limit_per_minute

    @app.middleware("http")
    async def _rate_limit_middleware(request: Request, call_next):
        if settings.chromagora_env == "development" and not settings.enforce_rate_limit:
            return await call_next(request)

        # Skip health and docs
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json", "/favicon.ico"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = 60.0  # 1 minute

        with _lock:
            timestamps = _requests[client_ip]
            # Remove old entries outside the window
            cutoff = now - window
            _requests[client_ip] = [t for t in timestamps if t > cutoff]
            timestamps = _requests[client_ip]

            if len(timestamps) >= rate:
                retry_after = int(timestamps[0] + window - now) + 1
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": f"Rate limit exceeded. Retry after {retry_after}s."},
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)

        return await call_next(request)
