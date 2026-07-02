"""Operational supervision for Demo Factory workers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID


STAGE_TIMEOUT_SECONDS = {
    "crawler": 420,
    "brand_synthesis": 420,
    "conversion_strategy": 480,
    "site_architecture": 360,
    "asset_curation": 480,
    "review_evidence": 600,
    "site_spec": 300,
    "rendering": 180,
    "adversarial_checker": 420,
    "visual_qa": 900,
    "publishing": 180,
}


@dataclass(frozen=True)
class StageTimeoutPolicy:
    stage: str
    soft_timeout_seconds: int
    hard_timeout_seconds: int


def timeout_policy(stage: str) -> StageTimeoutPolicy:
    soft = STAGE_TIMEOUT_SECONDS.get(stage, 420)
    return StageTimeoutPolicy(stage=stage, soft_timeout_seconds=soft, hard_timeout_seconds=soft * 2)


def classify_stage_timeout(stage: str, elapsed_seconds: int | float) -> str:
    policy = timeout_policy(stage)
    if elapsed_seconds >= policy.hard_timeout_seconds:
        return "hard_timeout"
    if elapsed_seconds >= policy.soft_timeout_seconds:
        return "soft_timeout"
    return "ok"


def is_rate_limit_error(error: BaseException | str | dict[str, Any]) -> bool:
    if isinstance(error, dict):
        if error.get("http_status") == 429 or error.get("status_code") == 429:
            return True
        text = " ".join(str(v) for v in error.values())
    else:
        text = str(error)
    lowered = text.lower()
    return "429" in lowered or "rate limit" in lowered or "too many requests" in lowered


def record_supervisor_event(
    *,
    sb,
    tenant_id: UUID,
    event_type: str,
    project_id: UUID | str | None = None,
    batch_id: UUID | str | None = None,
    stage: str | None = None,
    severity: str = "info",
    message: str | None = None,
    payload_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "tenant_id": str(tenant_id),
        "project_id": str(project_id) if project_id else None,
        "batch_id": str(batch_id) if batch_id else None,
        "event_type": event_type,
        "severity": severity,
        "stage": stage,
        "message": message,
        "payload_json": payload_json or {},
    }
    resp = sb.table("demo_factory_supervisor_events").insert(payload).execute()
    return (resp.data or [payload])[0]


def handle_rate_limit(
    *,
    sb,
    tenant_id: UUID,
    project_id: UUID | str,
    batch_id: UUID | str | None,
    stage: str,
    cooldown_seconds: int = 120,
    error: str = "Provider rate limit",
) -> dict[str, Any]:
    resume_after = datetime.now(timezone.utc) + timedelta(seconds=cooldown_seconds)
    sb.table("demo_site_projects").update(
        {"status": "waiting_rate_limit", "current_stage": stage, "error_message": error[:2000]}
    ).eq("id", str(project_id)).execute()
    if batch_id:
        sb.table("demo_site_batches").update({"status": "paused"}).eq("id", str(batch_id)).execute()
    event = record_supervisor_event(
        sb=sb,
        tenant_id=tenant_id,
        event_type="provider_rate_limited",
        project_id=project_id,
        batch_id=batch_id,
        stage=stage,
        severity="warning",
        message=error,
        payload_json={"cooldown_seconds": cooldown_seconds, "resume_after": resume_after.isoformat()},
    )
    return {"status": "waiting_rate_limit", "resume_after": resume_after.isoformat(), "event": event}


def is_retryable_failure(error: BaseException | str | dict[str, Any]) -> bool:
    if is_rate_limit_error(error):
        return True
    text = str(error).lower()
    return any(token in text for token in ["timeout", "temporarily", "connection", "5xx", "503", "502"])
