"""Demo Factory project stage machine."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from chromagora_api.services.demo_deployment_service import publish_demo
from chromagora_api.services.demo_frameworks import retrieve_framework_patterns

from chromagora_workers.demo_factory.agents.adversarial_checker_agent import run_adversarial_checker_agent
from chromagora_workers.demo_factory.agents.asset_curation_agent import run_asset_curation_agent
from chromagora_workers.demo_factory.agents.brand_synthesis_agent import run_brand_synthesis_agent
from chromagora_workers.demo_factory.agents.conversion_strategy_agent import run_conversion_strategy_agent
from chromagora_workers.demo_factory.agents.review_evidence_agent import run_review_evidence_agent
from chromagora_workers.demo_factory.agents.site_architecture_agent import run_site_architecture_agent
from chromagora_workers.demo_factory.evidence_bundle import build_evidence_bundle
from chromagora_workers.demo_factory.site_crawler import crawl_site
from chromagora_workers.demo_factory.site_spec_assembler import assemble_site_spec
from chromagora_workers.demo_factory.visual_qa import run_visual_qa


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase

    return get_backend_supabase()


def process_project(project_id: UUID | str, sb=None) -> dict[str, Any]:
    """Process one Demo Factory project through the v0.1 mocked pipeline."""
    sb = sb or _get_supabase()
    project = _load_project(sb, project_id)
    if not project:
        raise RuntimeError(f"Project not found: {project_id}")
    tenant_id = UUID(project["tenant_id"])
    project_uuid = UUID(project["id"])

    try:
        _set_stage(sb, project, "crawling", "prepare_project")
        _emit_event(sb, tenant_id, "demo_site.crawl_started", project)

        _set_stage(sb, project, "crawling", "crawl_site")
        crawl_site_result = crawl_site(sb=sb, tenant_id=tenant_id, project=project)
        snapshots = _load_project_rows(sb, project_uuid, "demo_site_source_snapshots")
        assets = _load_project_rows(sb, project_uuid, "demo_site_assets")
        _emit_event(
            sb,
            tenant_id,
            "demo_site.crawl_completed",
            project,
            {"page_count": crawl_site_result.get("page_count", len(snapshots))},
        )

        _set_stage(sb, project, "brand_synthesis", "build_evidence_bundle")
        evidence = build_evidence_bundle(project, snapshots=snapshots, assets=assets)

        _set_stage(sb, project, "brand_synthesis", "run_brand_synthesis")
        brand_doc = run_brand_synthesis_agent(project_id=project_uuid, evidence_bundle=evidence)
        brand_row = {
            "tenant_id": str(tenant_id),
            "project_id": str(project_uuid),
            "status": "current",
            "summary": f"Brand document for {project.get('business_name')}",
            "document_json": brand_doc.model_dump(mode="json"),
            "evidence_refs_json": brand_doc.evidence_references,
        }
        sb.table("demo_site_brand_documents").insert(brand_row).execute()
        _emit_event(sb, tenant_id, "demo_site.brand_doc_created", project)

        _set_stage(sb, project, "copy_strategy", "retrieve_frameworks")
        patterns = retrieve_framework_patterns(
            sb=sb,
            tenant_id=tenant_id,
            project_id=project_uuid,
            query_json={"business_vertical": brand_doc.vertical, "mock": True},
        )

        _set_stage(sb, project, "copy_strategy", "run_conversion_strategy")
        conversion = run_conversion_strategy_agent(
            project_id=project_uuid,
            brand_document=brand_doc,
            evidence_bundle=evidence,
            framework_patterns=patterns,
        )
        _emit_event(sb, tenant_id, "demo_site.copy_strategy_created", project)

        _set_stage(sb, project, "review_evidence", "run_review_evidence")
        review_evidence = run_review_evidence_agent(project_id=project_uuid, evidence_bundle=evidence)
        _persist_review_evidence(sb, tenant_id, project_uuid, review_evidence)

        _set_stage(sb, project, "site_architecture", "run_site_architecture")
        architecture = run_site_architecture_agent(
            project_id=project_uuid,
            conversion_strategy=conversion,
            review_evidence=review_evidence,
            demo_angle=evidence.get("demo_angle"),
        )

        _set_stage(sb, project, "asset_curation", "run_asset_curation")
        asset_map = run_asset_curation_agent(
            project_id=project_uuid,
            evidence_bundle=evidence,
            brand_document=brand_doc,
            site_architecture=architecture,
        )

        _set_stage(sb, project, "site_spec", "assemble_site_spec")
        site_spec, spec_row = assemble_site_spec(
            sb=sb,
            tenant_id=tenant_id,
            project=project,
            brand_document=brand_doc,
            conversion_strategy=conversion,
            site_architecture=architecture,
            asset_map=asset_map,
            review_evidence=review_evidence,
            evidence_bundle=evidence,
        )
        _emit_event(sb, tenant_id, "demo_site.site_spec_created", project, {"spec_id": spec_row["id"]})

        _set_stage(sb, project, "qa", "run_adversarial_checker")
        adversarial = run_adversarial_checker_agent(project_id=project_uuid, site_spec=site_spec)
        _persist_adversarial_report(sb, tenant_id, project_uuid, UUID(spec_row["id"]), adversarial)
        if not adversarial.passed:
            _emit_event(sb, tenant_id, "demo_site.qa_failed", project, {"blocking": adversarial.blocking_issues})
            raise RuntimeError("; ".join(adversarial.blocking_issues))

        _set_stage(sb, project, "qa", "run_visual_qa")
        qa_report = run_visual_qa(
            sb=sb,
            tenant_id=tenant_id,
            project_id=project_uuid,
            spec_id=UUID(spec_row["id"]),
            site_spec=site_spec,
        )
        if qa_report["status"] == "failed":
            _emit_event(sb, tenant_id, "demo_site.qa_failed", project, {"blocking": qa_report["blocking_issues_json"]})
            raise RuntimeError("; ".join(qa_report["blocking_issues_json"]))
        sb.table("demo_site_specs").update({"status": "qa_passed"}).eq("id", spec_row["id"]).execute()
        _emit_event(sb, tenant_id, "demo_site.qa_passed", project, {"spec_id": spec_row["id"]})

        _set_stage(sb, project, "publishing", "publish_demo")
        deployment = publish_demo(
            sb=sb,
            tenant_id=tenant_id,
            project_id=project_uuid,
            spec_id=UUID(spec_row["id"]),
            demo_slug=project["demo_slug"],
            verify_url=bool(os.getenv("DEMO_FACTORY_PUBLIC_BASE_URL")),
        )
        _set_stage(sb, project, "published", "mark_published")
        return {"status": "published", "project_id": str(project_uuid), "deployment": deployment}
    except Exception as exc:
        message = str(exc)[:2000]
        sb.table("demo_site_projects").update(
            {"status": "failed_retryable", "current_stage": "failed_retryable", "error_message": message}
        ).eq("id", str(project_id)).execute()
        _emit_event(sb, tenant_id, "demo_site.project_failed", project, {"error": message})
        raise


def _load_project(sb, project_id: UUID | str) -> dict[str, Any] | None:
    resp = sb.table("demo_site_projects").select("*").eq("id", str(project_id)).execute()
    return resp.data[0] if resp.data else None


def _load_project_rows(sb, project_id: UUID, table: str) -> list[dict[str, Any]]:
    resp = sb.table(table).select("*").eq("project_id", str(project_id)).execute()
    return resp.data or []


def _set_stage(sb, project: dict[str, Any], status: str, stage: str) -> None:
    update = {"status": status, "current_stage": stage}
    if not project.get("started_at"):
        update["started_at"] = _now()
    sb.table("demo_site_projects").update(update).eq("id", project["id"]).execute()
    project.update(update)


def _emit_event(
    sb,
    tenant_id: UUID,
    event_type: str,
    project: dict[str, Any],
    payload_json: dict[str, Any] | None = None,
) -> None:
    try:
        sb.table("events").insert(
            {
                "tenant_id": str(tenant_id),
                "event_type": event_type,
                "source_type": "demo_factory",
                "entity_type": "demo_site_project",
                "entity_id": project["id"],
                "trace_id": project.get("trace_id"),
                "payload_json": {
                    "project_id": project["id"],
                    "batch_id": project.get("batch_id"),
                    "batch_row_id": project.get("batch_row_id"),
                    **(payload_json or {}),
                },
                "idempotency_key": f"{event_type}:{project['id']}:{project.get('current_stage')}",
            }
        ).execute()
    except Exception:
        pass


def _persist_adversarial_report(sb, tenant_id: UUID, project_id: UUID, spec_id: UUID, report) -> None:
    sb.table("demo_site_qa_reports").insert(
        {
            "tenant_id": str(tenant_id),
            "project_id": str(project_id),
            "spec_id": str(spec_id),
            "report_type": "adversarial",
            "status": "passed" if report.passed else "failed",
            "blocking_issues_json": report.blocking_issues,
            "warnings_json": report.warnings,
            "screenshots_json": [],
            "report_json": report.model_dump(mode="json"),
        }
    ).execute()


def _persist_review_evidence(sb, tenant_id: UUID, project_id: UUID, review_evidence) -> None:
    for review in review_evidence.selected_reviews:
        sb.table("demo_site_reviews").insert(
            {
                "tenant_id": str(tenant_id),
                "project_id": str(project_id),
                "source_name": None,
                "source_url": review.source_url,
                "reviewer_name": review.reviewer_name,
                "rating": review.rating,
                "review_text": review.review_text,
                "review_date": review.review_date.isoformat() if review.review_date else None,
                "identity_match_json": review.identity_match_signals,
                "confidence_score": review.confidence_score,
                "status": "selected",
            }
        ).execute()
    for rejected in review_evidence.rejected_reviews[:20]:
        sb.table("demo_site_reviews").insert(
            {
                "tenant_id": str(tenant_id),
                "project_id": str(project_id),
                "source_name": rejected.get("source_name"),
                "source_url": rejected.get("source_url"),
                "reviewer_name": rejected.get("reviewer_name"),
                "review_text": rejected.get("review_text"),
                "identity_match_json": rejected.get("identity_match_signals") or {},
                "confidence_score": rejected.get("confidence_score"),
                "status": "rejected",
            }
        ).execute()
