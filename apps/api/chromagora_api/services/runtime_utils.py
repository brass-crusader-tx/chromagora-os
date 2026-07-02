"""Runtime hardening helpers for agent loops.

These helpers deliberately avoid framework dependencies so they can be used
from FastAPI routes, CLI workers, and tests.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
from datetime import date, datetime
from enum import Enum
from typing import Any, Awaitable, TypeVar
from uuid import UUID

T = TypeVar("T")


def run_awaitable_blocking(awaitable: Awaitable[T]) -> T:
    """Run an awaitable from sync code, even when a loop already exists.

    ``asyncio.run`` is fine in a CLI worker, but it fails inside an already
    running FastAPI event loop. In that case, run the coroutine on a short-lived
    thread with its own event loop. This is a transitional bridge until the
    quote runtime is fully async end-to-end.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result: dict[str, T] = {}
    error: dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            result["value"] = asyncio.run(awaitable)
        except BaseException as exc:  # pragma: no cover - re-raised below
            error["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in error:
        raise error["error"]
    return result["value"]


def to_jsonable(value: Any) -> Any:
    """Convert Pydantic/UUID/datetime-heavy objects into Supabase JSON values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def parse_json_field(value: Any, default: Any | None = None) -> Any:
    """Accept native JSON values and legacy JSON-encoded strings."""
    if value is None:
        return {} if default is None else default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {} if default is None else default
    return value


def stable_json_hash(value: Any) -> str:
    """Return a stable SHA-256 hash for JSON-like values."""
    canonical = json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
