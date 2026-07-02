"""Stale quote worker — runs detection and event processing on an interval.

This is still a polling worker, not Temporal/Durable Functions, but it now has
worker identity and heartbeat records so it can be observed and operated.

Usage:
    python -m chromagora_workers.stale_quote_worker [--interval SECONDS] [--once]
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
from uuid import UUID, uuid4

from dotenv import load_dotenv

# Resolve repo root from apps/workers/chromagora_workers/stale_quote_worker.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Ensure env is loaded before importing the API package.
env_candidates = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "apps" / "api" / ".env",
    Path.cwd() / ".env",
]
for env_path in env_candidates:
    if env_path.exists():
        load_dotenv(env_path)
        break

# Ensure we can import from sibling packages when running without installation.
for rel in ["apps/api", "packages/schemas", "packages/config", "packages/shared"]:
    sys.path.insert(0, str(PROJECT_ROOT / rel))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] worker: %(message)s",
)
logger = logging.getLogger(__name__)


def _get_supabase():
    from chromagora_api.core.supabase import get_supabase_admin
    sb = get_supabase_admin()
    if not sb:
        raise RuntimeError("Supabase not configured — check .env")
    return sb


def _default_worker_id() -> str:
    return f"stale-quote:{socket.gethostname()}:{os.getpid()}:{uuid4().hex[:8]}"


def _heartbeat(worker_id: str, status: str, last_cycle: dict | None = None, error: str | None = None) -> None:
    """Best-effort worker heartbeat. Safe if migration 000025 is not applied yet."""
    try:
        from chromagora_api.services.runtime_utils import to_jsonable
        sb = _get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        sb.table("worker_heartbeats").upsert({
            "worker_id": worker_id,
            "worker_type": "stale_quote_worker",
            "status": status,
            "last_heartbeat_at": now,
            "last_cycle_json": to_jsonable(last_cycle or {}),
            "last_error": error[:2000] if error else None,
        }, on_conflict="worker_id").execute()
    except Exception as exc:
        logger.debug("Heartbeat write skipped/failed: %s", exc)


def get_active_business_ids() -> list[str]:
    """Get all business IDs for the active tenant."""
    from chromagora_api.db.tenant import get_active_business_ids
    sb = _get_supabase()
    return get_active_business_ids(sb)


def run_detection_cycle(business_id: str) -> dict:
    """Run stale detection for a single business."""
    from chromagora_api.db.tenant import get_business_tenant_id
    from chromagora_api.services.quote_stale_detector import detect_stale_quotes

    sb = _get_supabase()
    tenant_id = get_business_tenant_id(business_id, sb)
    if not tenant_id:
        return {"business_id": business_id, "error": "Tenant not found"}

    results = detect_stale_quotes(
        business_id=UUID(business_id),
        tenant_id=UUID(tenant_id),
    )
    return {
        "business_id": business_id,
        "detected": len(results),
        "results": results,
    }


def run_event_processing(event_type: str | None = None, limit: int = 50, worker_id: str | None = None) -> dict:
    """Process pending events."""
    from chromagora_api.services.event_dispatcher import process_pending_events

    results = process_pending_events(event_type=event_type, limit=limit, worker_id=worker_id)
    processed_count = sum(1 for r in results if r.get("status") in {"processed", "no_handler"})
    failed_count = sum(1 for r in results if r.get("status") == "failed")
    return {
        "processed": processed_count,
        "failed": failed_count,
        "results": results,
    }


def run_full_cycle(worker_id: str | None = None, event_type: str | None = None) -> dict:
    """Run one full cycle: detect stale quotes for all businesses, then process events."""
    cycle_results = {
        "detection": [],
        "events": None,
        "errors": [],
    }

    try:
        business_ids = get_active_business_ids()
    except Exception as exc:
        cycle_results["errors"].append(f"Failed to load businesses: {exc}")
        return cycle_results

    for biz_id in business_ids:
        try:
            result = run_detection_cycle(biz_id)
            cycle_results["detection"].append(result)
            if result.get("detected", 0) > 0:
                logger.info("Detected %d stale quotes for business %s", result["detected"], biz_id[:8])
        except Exception as exc:
            error_msg = f"Detection failed for {biz_id}: {exc}"
            logger.error(error_msg)
            cycle_results["errors"].append(error_msg)

    try:
        event_results = run_event_processing(event_type=event_type, worker_id=worker_id)
        cycle_results["events"] = event_results
        if event_results.get("processed", 0) > 0 or event_results.get("failed", 0) > 0:
            logger.info(
                "Events: processed=%d failed=%d",
                event_results.get("processed", 0),
                event_results.get("failed", 0),
            )
    except Exception as exc:
        error_msg = f"Event processing failed: {exc}"
        logger.error(error_msg)
        cycle_results["errors"].append(error_msg)

    return cycle_results


def main():
    parser = argparse.ArgumentParser(description="Stale quote detection worker")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between cycles")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--event-type", type=str, default=None, help="Only process events of this type")
    parser.add_argument("--worker-id", type=str, default=None, help="Stable worker identity for claims/heartbeats")
    args = parser.parse_args()

    worker_id = args.worker_id or _default_worker_id()
    logger.info("Stale quote worker starting (worker_id=%s interval=%ds)", worker_id, args.interval)
    _heartbeat(worker_id, "starting")

    if args.once:
        results = run_full_cycle(worker_id=worker_id, event_type=args.event_type)
        status = "failed" if results.get("errors") else "stopped"
        _heartbeat(worker_id, status, last_cycle=results, error="; ".join(results.get("errors", [])) or None)
        logger.info("Cycle complete: %s", results)
        return results

    while True:
        try:
            results = run_full_cycle(worker_id=worker_id, event_type=args.event_type)
            detected = sum(d.get("detected", 0) for d in results["detection"])
            processed = (results.get("events") or {}).get("processed", 0)
            failed = (results.get("events") or {}).get("failed", 0)
            errors = len(results.get("errors", []))
            status = "failed" if errors else "running"
            _heartbeat(worker_id, status, last_cycle=results, error="; ".join(results.get("errors", [])) or None)

            if detected > 0 or processed > 0 or failed > 0 or errors > 0:
                logger.info("Cycle: detected=%d processed=%d failed=%d errors=%d", detected, processed, failed, errors)
        except Exception as exc:
            logger.exception("Cycle failed: %s", exc)
            _heartbeat(worker_id, "failed", error=str(exc))

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
