"""Demo Factory worker.

Usage:
    python -m chromagora_workers.demo_factory_worker [--interval SECONDS] [--once] [--auto-start]
"""

from __future__ import annotations

import argparse
import logging
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]

for env_path in [PROJECT_ROOT / ".env", PROJECT_ROOT / "apps" / "api" / ".env", Path.cwd() / ".env"]:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

for rel in ["apps/api", "packages/schemas", "packages/config", "packages/shared", "apps/workers"]:
    sys.path.insert(0, str(PROJECT_ROOT / rel))

from chromagora_workers.demo_factory.batch_processor import (  # noqa: E402
    get_next_row,
    mark_row_failed_terminal,
    mark_row_failed_retryable,
    mark_row_published,
    mark_row_running,
    maybe_complete_batch,
    update_batch_counts,
)
from chromagora_workers.demo_factory.orchestrator import process_project  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] demo-factory: %(message)s")
logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.core.supabase import get_supabase_admin

    sb = get_supabase_admin()
    if not sb:
        raise RuntimeError("Supabase not configured — check .env")
    return sb


def _default_worker_id() -> str:
    return f"demo-factory:{socket.gethostname()}:{os.getpid()}:{uuid4().hex[:8]}"


def _heartbeat(worker_id: str, status: str, last_cycle: dict | None = None, error: str | None = None) -> None:
    try:
        from chromagora_api.services.runtime_utils import to_jsonable

        sb = _get_supabase()
        sb.table("worker_heartbeats").upsert(
            {
                "worker_id": worker_id,
                "worker_type": "demo_factory_worker",
                "status": status,
                "last_heartbeat_at": datetime.now(timezone.utc).isoformat(),
                "last_cycle_json": to_jsonable(last_cycle or {}),
                "last_error": error[:2000] if error else None,
            },
            on_conflict="worker_id",
        ).execute()
    except Exception as exc:
        logger.debug("Heartbeat write skipped/failed: %s", exc)


def _load_active_batch(sb, auto_start: bool) -> dict | None:
    running = (
        sb.table("demo_site_batches")
        .select("*")
        .eq("status", "running")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if running.data:
        return running.data[0]
    if not auto_start:
        return None
    queued = (
        sb.table("demo_site_batches")
        .select("*")
        .eq("status", "queued")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if not queued.data:
        return None
    batch = queued.data[0]
    sb.table("demo_site_batches").update(
        {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", batch["id"]).execute()
    batch["status"] = "running"
    return batch


def _schema_unavailable(exc: Exception) -> bool:
    message = str(exc)
    return "PGRST205" in message or "Could not find the table" in message


def run_batch_cycle(worker_id: str | None = None, auto_start: bool = False) -> dict:
    sb = _get_supabase()
    try:
        batch = _load_active_batch(sb, auto_start=auto_start)
    except Exception as exc:
        if _schema_unavailable(exc):
            message = (
                "Demo Factory schema unavailable. Apply migrations "
                "000026_demo_factory.sql and 000027_demo_engine_finish_buildout.sql."
            )
            logger.warning("%s Raw error: %s", message, str(exc)[:500])
            return {"status": "schema_unavailable", "processed": 0, "error": message}
        raise
    if not batch:
        return {"status": "idle", "processed": 0}

    row = get_next_row(sb, batch["id"])
    if not row:
        update_batch_counts(sb, batch["id"])
        completed = maybe_complete_batch(sb, batch["id"])
        return {"status": "completed" if completed else "idle", "batch_id": batch["id"], "processed": 0}

    logger.info("Processing batch=%s row=%s project=%s", batch["id"], row.get("row_number"), row.get("project_id"))
    running_row = mark_row_running(sb, row["id"]) or row
    try:
        result = process_project(row["project_id"], sb=sb)
        mark_row_published(sb, row["id"])
        update_batch_counts(sb, batch["id"])
        maybe_complete_batch(sb, batch["id"])
        return {"status": "processed", "batch_id": batch["id"], "row_id": row["id"], "result": result}
    except Exception as exc:
        max_attempts = max(1, int(os.getenv("DEMO_FACTORY_MAX_ROW_ATTEMPTS", "3")))
        attempt_count = int(running_row.get("attempt_count") or 1)
        if attempt_count >= max_attempts:
            mark_row_failed_terminal(sb, row["id"], str(exc))
            status = "failed_terminal"
        else:
            mark_row_failed_retryable(sb, row["id"], str(exc))
            status = "failed_retryable"
        update_batch_counts(sb, batch["id"])
        maybe_complete_batch(sb, batch["id"])
        logger.exception("Demo row failed with status=%s: %s", status, exc)
        return {"status": status, "batch_id": batch["id"], "row_id": row["id"], "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description="Demo Factory sequential worker")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--auto-start", action="store_true", help="Start the oldest queued batch when no batch is running")
    parser.add_argument("--worker-id", type=str, default=None, help="Stable worker identity for heartbeats")
    args = parser.parse_args()

    worker_id = args.worker_id or _default_worker_id()
    logger.info("Demo Factory worker starting (worker_id=%s interval=%ds)", worker_id, args.interval)
    _heartbeat(worker_id, "starting")

    if args.once:
        result = run_batch_cycle(worker_id=worker_id, auto_start=args.auto_start)
        _heartbeat(worker_id, "stopped", last_cycle=result, error=result.get("error"))
        logger.info("Cycle complete: %s", result)
        return result

    while True:
        try:
            result = run_batch_cycle(worker_id=worker_id, auto_start=args.auto_start)
            _heartbeat(worker_id, "running", last_cycle=result, error=result.get("error"))
            if result.get("status") != "idle":
                logger.info("Cycle: %s", result)
        except Exception as exc:
            logger.exception("Cycle failed: %s", exc)
            _heartbeat(worker_id, "failed", error=str(exc))
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
