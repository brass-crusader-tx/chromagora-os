"""Demo Factory routes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from chromagora_api.db.tenant import DatabaseUnavailable, TenantError, get_active_tenant_id, get_backend_supabase
from chromagora_api.services.demo_deployment_service import publish_demo
from chromagora_api.services.demo_factory_importer import import_demo_csv
from chromagora_api.services.demo_link_drop_importer import DemoLinkDropInput, import_demo_link_drop
from chromagora_schemas.demo_factory import SiteSpec

router = APIRouter(prefix="/demo-sites", tags=["demo-sites"])


class SiteSpecUpdateRequest(BaseModel):
    spec_id: UUID | None = None
    spec_json: dict[str, Any]
    republish: bool = False


class OperatorReviewRequest(BaseModel):
    sendability_status: str
    sendability_score: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    checks: dict[str, bool] = Field(default_factory=dict)


def _scoped_db():
    try:
        sb = get_backend_supabase()
        tenant_id = UUID(get_active_tenant_id(sb))
        return sb, tenant_id
    except TenantError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _schema_unavailable(exc: Exception) -> bool:
    message = str(exc)
    return "PGRST205" in message or "Could not find the table" in message


def _raise_schema_unavailable() -> None:
    raise HTTPException(
        status_code=503,
        detail="Demo Factory database schema unavailable. Apply migrations 000026 and 000027.",
    )


async def _csv_body_from_request(request: Request) -> tuple[bytes, str]:
    content_type = request.headers.get("content-type", "")
    filename = request.headers.get("x-filename") or "demo-factory-import.csv"
    body = await request.body()
    if "application/json" in content_type:
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}")
        csv_text = payload.get("csv") or payload.get("content")
        if not csv_text:
            raise HTTPException(status_code=400, detail="JSON body must include csv or content")
        filename = payload.get("source_filename") or filename
        return str(csv_text).encode("utf-8"), filename
    if not body.strip():
        raise HTTPException(status_code=400, detail="CSV body is empty")
    return body, filename


@router.post("/import-csv")
async def import_csv(request: Request, x_filename: str | None = Header(default=None)):
    sb, tenant_id = _scoped_db()
    csv_bytes, filename = await _csv_body_from_request(request)
    if x_filename:
        filename = x_filename
    try:
        return import_demo_csv(
            csv_bytes=csv_bytes,
            source_filename=filename,
            tenant_id=tenant_id,
            sb=sb,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {exc}")


@router.get("/tls-ask")
async def tls_ask(domain: str):
    hostname = domain.strip().lower().rstrip(".")
    if hostname.endswith(".demo.chromagora.com") and hostname != "demo.chromagora.com":
        return Response(status_code=200)
    return Response(status_code=403)


@router.post("/import-link")
async def import_link(payload: DemoLinkDropInput):
    sb, tenant_id = _scoped_db()
    try:
        result = import_demo_link_drop(payload=payload, tenant_id=tenant_id, sb=sb)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Link import failed: {exc}")

    if payload.auto_start and result.get("batch", {}).get("id"):
        batch_id = UUID(result["batch"]["id"])
        update = {"status": "running", "started_at": _now()}
        resp = (
            sb.table("demo_site_batches")
            .update(update)
            .eq("tenant_id", str(tenant_id))
            .eq("id", str(batch_id))
            .execute()
        )
        if resp.data:
            result["batch"] = resp.data[0]
        else:
            result["batch"].update(update)
        _emit_batch_event(sb, tenant_id, batch_id, "demo_site.batch_started")

    return result


@router.get("/batches")
async def list_batches(limit: int = 25):
    sb, tenant_id = _scoped_db()
    resp = (
        sb.table("demo_site_batches")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: UUID):
    sb, tenant_id = _scoped_db()
    batch_resp = (
        sb.table("demo_site_batches")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(batch_id))
        .execute()
    )
    if not batch_resp.data:
        raise HTTPException(status_code=404, detail="Batch not found")

    rows_resp = (
        sb.table("demo_site_batch_rows")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("batch_id", str(batch_id))
        .order("row_number", desc=False)
        .execute()
    )
    rows = rows_resp.data or []
    project_ids = [row["project_id"] for row in rows if row.get("project_id")]
    projects_by_id: dict[str, dict] = {}
    if project_ids:
        projects_resp = (
            sb.table("demo_site_projects")
            .select("*")
            .eq("tenant_id", str(tenant_id))
            .in_("id", project_ids)
            .execute()
        )
        projects_by_id = {row["id"]: row for row in (projects_resp.data or [])}

    for row in rows:
        row["project"] = projects_by_id.get(row.get("project_id"))

    return {"batch": batch_resp.data[0], "rows": rows}


@router.post("/batches/{batch_id}/start")
async def start_batch(batch_id: UUID):
    sb, tenant_id = _scoped_db()
    resp = (
        sb.table("demo_site_batches")
        .update({"status": "running", "started_at": _now()})
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(batch_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    _emit_batch_event(sb, tenant_id, batch_id, "demo_site.batch_started")
    return resp.data[0]


@router.post("/batches/{batch_id}/pause")
async def pause_batch(batch_id: UUID):
    return _update_batch_status(batch_id, "paused")


@router.post("/batches/{batch_id}/resume")
async def resume_batch(batch_id: UUID):
    sb, tenant_id = _scoped_db()
    resp = (
        sb.table("demo_site_batches")
        .update({"status": "running"})
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(batch_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    _emit_batch_event(sb, tenant_id, batch_id, "demo_site.batch_started")
    return resp.data[0]


@router.post("/dev/run-worker-once")
async def run_worker_once_dev(auto_start: bool = True):
    if os.getenv("DEMO_FACTORY_ENABLE_DEV_CONTROLS", "").lower() not in {"1", "true", "yes"}:
        raise HTTPException(status_code=404, detail="Not found")
    from chromagora_workers.demo_factory_worker import run_batch_cycle

    return run_batch_cycle(worker_id="api-dev-control", auto_start=auto_start)


def _update_batch_status(batch_id: UUID, status: str):
    sb, tenant_id = _scoped_db()
    resp = (
        sb.table("demo_site_batches")
        .update({"status": status})
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(batch_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    return resp.data[0]


@router.get("/projects/{project_id}")
async def get_project(project_id: UUID):
    sb, tenant_id = _scoped_db()
    resp = (
        sb.table("demo_site_projects")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(project_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return resp.data[0]


@router.post("/projects/{project_id}/retry")
async def retry_project(project_id: UUID):
    sb, tenant_id = _scoped_db()
    project = await get_project(project_id)
    update = {"status": "queued", "current_stage": "queued", "error_message": None}
    resp = (
        sb.table("demo_site_projects")
        .update(update)
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(project_id))
        .execute()
    )
    if project.get("batch_row_id"):
        sb.table("demo_site_batch_rows").update({"status": "queued", "last_error": None}).eq(
            "id", project["batch_row_id"]
        ).execute()
    return resp.data[0] if resp.data else {**project, **update}


@router.post("/projects/{project_id}/archive")
async def archive_project(project_id: UUID):
    sb, tenant_id = _scoped_db()
    project = await get_project(project_id)
    resp = (
        sb.table("demo_site_projects")
        .update({"status": "archived", "current_stage": "archived"})
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(project_id))
        .execute()
    )
    if project.get("batch_row_id"):
        sb.table("demo_site_batch_rows").update({"status": "skipped"}).eq("id", project["batch_row_id"]).execute()
    return resp.data[0] if resp.data else {**project, "status": "archived", "current_stage": "archived"}


@router.get("/projects/{project_id}/artifacts")
async def get_project_artifacts(project_id: UUID):
    sb, tenant_id = _scoped_db()
    await get_project(project_id)
    return {
        "brand_documents": _load_project_table(sb, tenant_id, project_id, "demo_site_brand_documents"),
        "assets": _load_project_table(sb, tenant_id, project_id, "demo_site_assets"),
        "reviews": _load_project_table(sb, tenant_id, project_id, "demo_site_reviews"),
        "site_specs": _load_project_table(sb, tenant_id, project_id, "demo_site_specs"),
        "model_calls": _load_project_table(sb, tenant_id, project_id, "demo_model_calls"),
        "supervisor_events": _load_project_table(sb, tenant_id, project_id, "demo_factory_supervisor_events"),
    }


@router.get("/projects/{project_id}/qa")
async def get_project_qa(project_id: UUID):
    sb, tenant_id = _scoped_db()
    await get_project(project_id)
    return _load_project_table(sb, tenant_id, project_id, "demo_site_qa_reports")


@router.get("/projects/{project_id}/deployment")
async def get_project_deployment(project_id: UUID):
    sb, tenant_id = _scoped_db()
    await get_project(project_id)
    rows = _load_project_table(sb, tenant_id, project_id, "demo_site_deployments")
    return rows[0] if rows else None


@router.get("/projects/{project_id}/site-specs")
async def get_project_site_specs(project_id: UUID):
    sb, tenant_id = _scoped_db()
    await get_project(project_id)
    rows = _load_project_table(sb, tenant_id, project_id, "demo_site_specs")
    return [
        {
            "id": row.get("id"),
            "version": row.get("version"),
            "status": row.get("status"),
            "is_current": row.get("is_current"),
            "created_at": row.get("created_at"),
            "published_at": row.get("published_at"),
            "metadata": (row.get("spec_json") or {}).get("metadata") or {},
        }
        for row in rows
    ]


@router.patch("/projects/{project_id}/site-spec")
async def update_project_site_spec(project_id: UUID, payload: SiteSpecUpdateRequest):
    sb, tenant_id = _scoped_db()
    project = await get_project(project_id)
    try:
        spec = SiteSpec.model_validate(payload.spec_json)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid SiteSpec: {exc}")
    if str(spec.project_id) != str(project_id):
        raise HTTPException(status_code=400, detail="SiteSpec project_id does not match project")

    base_rows = _load_project_table(sb, tenant_id, project_id, "demo_site_specs")
    base_version = max([int(row.get("version") or 0) for row in base_rows] or [0])
    spec.metadata = {
        **(spec.metadata or {}),
        "edited_by_operator": True,
        "edited_from_spec_id": str(payload.spec_id) if payload.spec_id else None,
        "edited_at": _now(),
    }
    spec_row = {
        "id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "project_id": str(project_id),
        "status": "draft",
        "spec_json": spec.model_dump(mode="json"),
        "version": base_version + 1,
        "is_current": False,
    }
    sb.table("demo_site_specs").insert(spec_row).execute()
    if payload.republish:
        deployment = _qa_and_publish_spec(
            sb=sb,
            tenant_id=tenant_id,
            project=project,
            spec_id=UUID(spec_row["id"]),
            site_spec=spec,
        )
        return {"site_spec_row": spec_row, "deployment": deployment}
    return {"site_spec_row": spec_row, "site_spec": spec_row["spec_json"]}


@router.post("/projects/{project_id}/publish-spec/{spec_id}")
async def publish_project_site_spec(project_id: UUID, spec_id: UUID):
    sb, tenant_id = _scoped_db()
    project = await get_project(project_id)
    spec_row = _load_spec_row(sb, tenant_id, project_id, spec_id)
    try:
        spec = SiteSpec.model_validate(spec_row["spec_json"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid SiteSpec: {exc}")
    deployment = _qa_and_publish_spec(
        sb=sb,
        tenant_id=tenant_id,
        project=project,
        spec_id=spec_id,
        site_spec=spec,
    )
    return {"deployment": deployment}


@router.post("/projects/{project_id}/operator-review")
async def operator_review(project_id: UUID, payload: OperatorReviewRequest):
    allowed = {"unreviewed", "needs_edits", "sendable", "sent", "archived"}
    if payload.sendability_status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid sendability_status")
    sb, tenant_id = _scoped_db()
    await get_project(project_id)
    update = {
        "sendability_status": payload.sendability_status,
        "sendability_score": payload.sendability_score,
        "operator_review_json": {
            "notes": payload.notes,
            "checks": payload.checks,
            "reviewed_at": _now(),
        },
    }
    resp = (
        sb.table("demo_site_projects")
        .update(update)
        .eq("tenant_id", str(tenant_id))
        .eq("id", str(project_id))
        .execute()
    )
    return (resp.data or [update])[0]


@router.get("/projects/{project_id}/site-spec-preview")
async def get_project_site_spec_preview(project_id: UUID, spec_id: UUID | None = None):
    sb, tenant_id = _scoped_db()
    project = await get_project(project_id)
    query = (
        sb.table("demo_site_specs")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("project_id", str(project_id))
    )
    if spec_id:
        query = query.eq("id", str(spec_id))
    else:
        query = query.order("created_at", desc=True).limit(1)
    resp = query.execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="SiteSpec not found")
    return {"project": project, "site_spec_row": resp.data[0], "site_spec": resp.data[0]["spec_json"]}


@router.get("/public/{slug}/site-spec")
async def get_public_site_spec(slug: str):
    sb, tenant_id = _scoped_db()
    try:
        deployment_resp = (
            sb.table("demo_site_deployments")
            .select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("demo_slug", slug)
            .eq("status", "published")
            .execute()
        )
    except Exception as exc:
        if _schema_unavailable(exc):
            _raise_schema_unavailable()
        raise
    if not deployment_resp.data:
        raise HTTPException(status_code=404, detail="Published demo not found")
    deployment = deployment_resp.data[0]
    try:
        spec_resp = (
            sb.table("demo_site_specs")
            .select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("id", deployment["spec_id"])
            .eq("is_current", True)
            .execute()
        )
    except Exception as exc:
        if _schema_unavailable(exc):
            _raise_schema_unavailable()
        raise
    if not spec_resp.data:
        raise HTTPException(status_code=404, detail="Current SiteSpec not found")
    return {"deployment": deployment, "site_spec": spec_resp.data[0]["spec_json"]}


def _load_project_table(sb, tenant_id: UUID, project_id: UUID, table: str) -> list[dict]:
    resp = (
        sb.table(table)
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


def _load_spec_row(sb, tenant_id: UUID, project_id: UUID, spec_id: UUID) -> dict:
    resp = (
        sb.table("demo_site_specs")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .eq("project_id", str(project_id))
        .eq("id", str(spec_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="SiteSpec not found")
    return resp.data[0]


def _qa_and_publish_spec(*, sb, tenant_id: UUID, project: dict, spec_id: UUID, site_spec: SiteSpec) -> dict:
    from chromagora_workers.demo_factory.agents.adversarial_checker_agent import run_adversarial_checker_agent
    from chromagora_workers.demo_factory.visual_qa import run_visual_qa

    project_id = UUID(project["id"])
    adversarial = run_adversarial_checker_agent(project_id=project_id, site_spec=site_spec)
    sb.table("demo_site_qa_reports").insert(
        {
            "tenant_id": str(tenant_id),
            "project_id": str(project_id),
            "spec_id": str(spec_id),
            "report_type": "adversarial",
            "status": "passed" if adversarial.passed else "failed",
            "blocking_issues_json": adversarial.blocking_issues,
            "warnings_json": adversarial.warnings,
            "screenshots_json": [],
            "report_json": adversarial.model_dump(mode="json"),
        }
    ).execute()
    if not adversarial.passed:
        raise HTTPException(status_code=400, detail={"qa_failed": adversarial.blocking_issues})

    visual = run_visual_qa(
        sb=sb,
        tenant_id=tenant_id,
        project_id=project_id,
        spec_id=spec_id,
        site_spec=site_spec,
    )
    if visual["status"] == "failed":
        raise HTTPException(status_code=400, detail={"qa_failed": visual["blocking_issues_json"]})
    sb.table("demo_site_specs").update({"status": "qa_passed"}).eq("id", str(spec_id)).execute()
    return publish_demo(
        sb=sb,
        tenant_id=tenant_id,
        project_id=project_id,
        spec_id=spec_id,
        demo_slug=project["demo_slug"],
        verify_url=bool(os.getenv("DEMO_FACTORY_PUBLIC_BASE_URL")),
    )


def _emit_batch_event(sb, tenant_id: UUID, batch_id: UUID, event_type: str) -> None:
    try:
        sb.table("events").insert(
            {
                "tenant_id": str(tenant_id),
                "event_type": event_type,
                "source_type": "demo_factory",
                "entity_type": "demo_site_batch",
                "entity_id": str(batch_id),
                "payload_json": {"batch_id": str(batch_id)},
                "idempotency_key": f"{event_type}:{batch_id}",
            }
        ).execute()
    except Exception:
        pass
