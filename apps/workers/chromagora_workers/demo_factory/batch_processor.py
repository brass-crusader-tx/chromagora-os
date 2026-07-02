"""Sequential Demo Factory batch processing helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID


RETRYABLE_ROW_STATUSES = {"queued", "failed_retryable"}
TERMINAL_ROW_STATUSES = {"published", "failed_terminal", "skipped"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_next_row(sb, batch_id: UUID | str) -> dict[str, Any] | None:
    """Return the next queued/retryable row in spreadsheet processing order."""
    resp = (
        sb.table("demo_site_batch_rows")
        .select("*")
        .eq("batch_id", str(batch_id))
        .order("row_number", desc=False)
        .execute()
    )
    for row in resp.data or []:
        status = row.get("status")
        if status in RETRYABLE_ROW_STATUSES:
            return row
        if status in {"running", "paused"}:
            return None
        if status not in TERMINAL_ROW_STATUSES:
            return None
    return None


def mark_row_running(sb, row_id: UUID | str) -> dict[str, Any] | None:
    row = _load_row(sb, row_id)
    if not row:
        return None
    attempt_count = int(row.get("attempt_count") or 0) + 1
    update = {
        "status": "running",
        "attempt_count": attempt_count,
        "started_at": row.get("started_at") or _now(),
        "last_error": None,
    }
    resp = sb.table("demo_site_batch_rows").update(update).eq("id", str(row_id)).execute()
    if row.get("project_id"):
        sb.table("demo_site_projects").update(
            {"status": "crawling", "current_stage": "prepare_project", "started_at": _now(), "error_message": None}
        ).eq("id", row["project_id"]).execute()
    if row.get("batch_id"):
        sb.table("demo_site_batches").update(
            {"current_row_number": row.get("row_number")}
        ).eq("id", row["batch_id"]).execute()
    return (resp.data or [{**row, **update}])[0]


def mark_row_published(sb, row_id: UUID | str) -> dict[str, Any] | None:
    update = {"status": "published", "completed_at": _now(), "last_error": None}
    resp = sb.table("demo_site_batch_rows").update(update).eq("id", str(row_id)).execute()
    row = (resp.data or [_load_row(sb, row_id) or {}])[0]
    if row.get("project_id"):
        sb.table("demo_site_projects").update(
            {"status": "published", "current_stage": "published", "completed_at": _now(), "error_message": None}
        ).eq("id", row["project_id"]).execute()
    return row


def mark_row_failed_retryable(sb, row_id: UUID | str, error: str) -> dict[str, Any] | None:
    return _mark_row_failed(sb, row_id, "failed_retryable", error)


def mark_row_failed_terminal(sb, row_id: UUID | str, error: str) -> dict[str, Any] | None:
    return _mark_row_failed(sb, row_id, "failed_terminal", error)


def _mark_row_failed(sb, row_id: UUID | str, status: str, error: str) -> dict[str, Any] | None:
    message = error[:2000]
    update = {"status": status, "last_error": message, "completed_at": _now()}
    resp = sb.table("demo_site_batch_rows").update(update).eq("id", str(row_id)).execute()
    row = (resp.data or [_load_row(sb, row_id) or {}])[0]
    if row.get("project_id"):
        sb.table("demo_site_projects").update(
            {"status": status, "current_stage": status, "error_message": message}
        ).eq("id", row["project_id"]).execute()
    return row


def update_batch_counts(sb, batch_id: UUID | str) -> dict[str, Any]:
    rows_resp = (
        sb.table("demo_site_batch_rows")
        .select("*")
        .eq("batch_id", str(batch_id))
        .order("row_number", desc=False)
        .execute()
    )
    rows = rows_resp.data or []
    queued_count = sum(1 for row in rows if row.get("status") in {"queued", "failed_retryable"})
    running_count = sum(1 for row in rows if row.get("status") == "running")
    published_count = sum(1 for row in rows if row.get("status") == "published")
    failed_count = sum(1 for row in rows if row.get("status") in {"failed_retryable", "failed_terminal"})
    current_row_number = next(
        (
            row.get("row_number")
            for row in rows
            if row.get("status") in {"queued", "running", "failed_retryable", "paused"}
        ),
        None,
    )
    update = {
        "total_rows": len(rows),
        "queued_count": queued_count,
        "running_count": running_count,
        "published_count": published_count,
        "failed_count": failed_count,
        "current_row_number": current_row_number,
    }
    resp = sb.table("demo_site_batches").update(update).eq("id", str(batch_id)).execute()
    return (resp.data or [update])[0]


def maybe_complete_batch(sb, batch_id: UUID | str) -> bool:
    rows_resp = sb.table("demo_site_batch_rows").select("*").eq("batch_id", str(batch_id)).execute()
    rows = rows_resp.data or []
    if not rows:
        return False
    if any(row.get("status") in {"queued", "running", "failed_retryable", "paused"} for row in rows):
        return False
    batch_resp = sb.table("demo_site_batches").select("*").eq("id", str(batch_id)).execute()
    batch = batch_resp.data[0] if batch_resp.data else {}
    sb.table("demo_site_batches").update(
        {"status": "completed", "completed_at": _now(), "current_row_number": None}
    ).eq("id", str(batch_id)).execute()
    _emit_batch_completed(sb, batch_id, batch)
    return True


def recover_stale_running_rows(sb, older_than_minutes: int) -> int:
    """Move stale running rows back to retryable failure so batches can progress."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
    resp = sb.table("demo_site_batch_rows").select("*").eq("status", "running").execute()
    recovered = 0
    for row in resp.data or []:
        started_at = _parse_datetime(row.get("started_at"))
        if started_at and started_at > cutoff:
            continue
        _mark_row_failed(sb, row["id"], "failed_retryable", "Recovered stale running row")
        recovered += 1
    return recovered


def _load_row(sb, row_id: UUID | str) -> dict[str, Any] | None:
    resp = sb.table("demo_site_batch_rows").select("*").eq("id", str(row_id)).execute()
    return resp.data[0] if resp.data else None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def _emit_batch_completed(sb, batch_id: UUID | str, batch: dict[str, Any]) -> None:
    tenant_id = batch.get("tenant_id")
    if not tenant_id:
        return
    try:
        sb.table("events").insert(
            {
                "tenant_id": tenant_id,
                "event_type": "demo_site.batch_completed",
                "source_type": "demo_factory",
                "entity_type": "demo_site_batch",
                "entity_id": str(batch_id),
                "payload_json": {"batch_id": str(batch_id)},
                "idempotency_key": f"demo_site.batch_completed:{batch_id}",
            }
        ).execute()
    except Exception:
        pass
