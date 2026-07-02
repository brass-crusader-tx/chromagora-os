"""Demo Factory publish/deployment helpers."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_demo(
    *,
    sb,
    tenant_id: UUID,
    project_id: UUID,
    spec_id: UUID,
    demo_slug: str,
    verify_url: bool = False,
) -> dict[str, Any]:
    """Mark a passing SiteSpec current and create/update a deployment row."""
    demo_host = f"{demo_slug}.demo.chromagora.com"
    demo_url = f"https://{demo_host}"
    verification_url = _verification_url(demo_slug, demo_url) if verify_url else None
    now = _now()

    sb.table("demo_site_specs").update({"is_current": False}).eq("project_id", str(project_id)).execute()
    sb.table("demo_site_specs").update(
        {"is_current": True, "status": "published", "published_at": now}
    ).eq("id", str(spec_id)).execute()

    deployment_payload = {
        "id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "project_id": str(project_id),
        "spec_id": str(spec_id),
        "demo_slug": demo_slug,
        "demo_host": demo_host,
        "demo_url": demo_url,
        "status": "published",
        "published_at": now,
        "verified_at": now if verify_url else None,
        "metadata_json": {
            "verification": "pending" if verify_url else "skipped",
            "verification_url": verification_url,
        },
    }

    existing = (
        sb.table("demo_site_deployments")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("demo_slug", demo_slug)
        .execute()
    )
    if existing.data:
        deployment_id = existing.data[0]["id"]
        resp = (
            sb.table("demo_site_deployments")
            .update({k: v for k, v in deployment_payload.items() if k != "id"})
            .eq("id", deployment_id)
            .execute()
        )
        deployment = (resp.data or [{**deployment_payload, "id": deployment_id}])[0]
    else:
        resp = sb.table("demo_site_deployments").insert(deployment_payload).execute()
        deployment = (resp.data or [deployment_payload])[0]

    if verify_url:
        try:
            verification_result = _verify_demo_url(verification_url or demo_url)
            verify_update = {
                "verified_at": _now(),
                "metadata_json": {
                    "verification": verification_result["status"],
                    "verification_url": verification_url,
                    "http_status": verification_result.get("http_status"),
                },
            }
            resp = sb.table("demo_site_deployments").update(verify_update).eq("id", deployment["id"]).execute()
            deployment = (resp.data or [{**deployment, **verify_update}])[0]
        except Exception as exc:
            sb.table("demo_site_deployments").update(
                {
                    "status": "failed",
                    "error_message": str(exc)[:2000],
                    "metadata_json": {
                        "verification": "failed",
                        "verification_url": verification_url,
                    },
                }
            ).eq("id", deployment["id"]).execute()
            sb.table("demo_site_specs").update({"is_current": False, "status": "qa_passed"}).eq(
                "id", str(spec_id)
            ).execute()
            raise

    sb.table("demo_site_projects").update(
        {
            "demo_host": demo_host,
            "status": "published",
            "current_stage": "published",
            "completed_at": now,
            "error_message": None,
        }
    ).eq("id", str(project_id)).execute()

    project_resp = sb.table("demo_site_projects").select("batch_row_id").eq("id", str(project_id)).execute()
    if project_resp.data and project_resp.data[0].get("batch_row_id"):
        sb.table("demo_site_batch_rows").update(
            {"status": "published", "completed_at": now, "last_error": None}
        ).eq("id", project_resp.data[0]["batch_row_id"]).execute()

    try:
        sb.table("events").insert(
            {
                "tenant_id": str(tenant_id),
                "event_type": "demo_site.published",
                "source_type": "demo_factory",
                "entity_type": "demo_site_project",
                "entity_id": str(project_id),
                "payload_json": {
                    "project_id": str(project_id),
                    "spec_id": str(spec_id),
                    "demo_slug": demo_slug,
                    "demo_url": demo_url,
                },
                "idempotency_key": f"demo_site.published:{project_id}:{spec_id}",
            }
        ).execute()
    except Exception:
        pass

    return deployment


def _verification_url(demo_slug: str, demo_url: str) -> str:
    public_base = os.getenv("DEMO_FACTORY_PUBLIC_BASE_URL")
    if public_base:
        return f"{public_base.rstrip('/')}/demo/{demo_slug}"
    return demo_url


def _verify_demo_url(url: str) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url)
    except Exception as exc:
        raise RuntimeError(f"Demo URL verification failed for {url}: {exc}") from exc
    if response.status_code >= 400:
        raise RuntimeError(f"Demo URL verification failed for {url}: HTTP {response.status_code}")
    return {"status": "passed", "http_status": response.status_code}
