"""Workflow API routes."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from chromagora_api.db.tenant import (
    DatabaseUnavailable,
    TenantError,
    get_active_tenant_id,
    get_backend_supabase,
    get_business_tenant_id,
)
from chromagora_api.services.workflows import (
    run_review_request_workflow,
    run_stale_quote_followup_workflow,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
async def list_workflow_definitions():
    """List workflow definitions enriched with active-tenant run metadata."""
    try:
        sb = get_backend_supabase()
        tenant_id = get_active_tenant_id(sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    defs_resp = (
        sb.table("workflow_definitions")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    runs_resp = (
        sb.table("workflow_runs")
        .select("workflow_definition_id, workflow_type, status, started_at, updated_at")
        .eq("tenant_id", tenant_id)
        .order("started_at", desc=True)
        .execute()
    )
    latest_by_def: dict[str, dict] = {}
    latest_by_type: dict[str, dict] = {}
    for run in runs_resp.data or []:
        if run.get("workflow_definition_id"):
            latest_by_def.setdefault(run["workflow_definition_id"], run)
        latest_by_type.setdefault(run.get("workflow_type", ""), run)

    results = []
    for row in defs_resp.data or []:
        latest = latest_by_def.get(row["id"]) or latest_by_type.get(row.get("workflow_type", ""))
        config = row.get("config_json") or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}
        steps = config.get("steps") if isinstance(config, dict) else None
        results.append({
            **row,
            "status": latest.get("status", "not_run") if latest else "not_run",
            "steps": len(steps) if isinstance(steps, list) else None,
            "last_run_at": (latest or {}).get("started_at") or (latest or {}).get("updated_at"),
        })
    return results


@router.post("")
async def create_workflow_definition(body: dict):
    """Create a new workflow definition."""
    try:
        sb = get_backend_supabase()
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    data = {
        "name": name,
        "description": body.get("description"),
        "workflow_type": body.get("workflow_type", "custom"),
        "config_json": body.get("definition", {}),
        "is_active": True,
    }
    resp = sb.table("workflow_definitions").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create workflow definition")
    return resp.data[0]


@router.post("/review-request/dry-run")
async def review_request_dry_run(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    job_summary: str,
    completed_at: str,
):
    """Execute the completed-job review-request workflow in dry-run mode."""
    try:
        sb = get_backend_supabase()
        tenant_id_raw = get_business_tenant_id(str(business_id), sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not tenant_id_raw:
        raise HTTPException(status_code=404, detail="Business not found")

    tenant_id = UUID(tenant_id_raw)
    result = run_review_request_workflow(
        tenant_id=tenant_id,
        business_id=business_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        job_summary=job_summary,
        completed_at=completed_at,
    )
    return result


@router.post("/stale-quote-followup/dry-run")
async def stale_quote_followup_dry_run(
    business_id: UUID,
    customer_name: str,
    customer_contact: str,
    service_type: str,
    quote_sent_at: str,
    quote_id: str | None = None,
    quote_amount: float | None = None,
    last_contact_at: str | None = None,
):
    """Execute the stale-quote follow-up workflow in dry-run mode."""
    try:
        sb = get_backend_supabase()
        tenant_id_raw = get_business_tenant_id(str(business_id), sb)
    except TenantError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not tenant_id_raw:
        raise HTTPException(status_code=404, detail="Business not found")

    tenant_id = UUID(tenant_id_raw)
    result = run_stale_quote_followup_workflow(
        tenant_id=tenant_id,
        business_id=business_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        service_type=service_type,
        quote_sent_at=quote_sent_at,
        quote_id=quote_id,
        quote_amount=quote_amount,
        last_contact_at=last_contact_at,
    )
    return result
