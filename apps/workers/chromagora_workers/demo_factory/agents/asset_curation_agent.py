"""Asset curation agent boundary."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from chromagora_schemas.demo_factory import AssetMap, BrandDocument, SiteArchitecturePlan

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback


def run_asset_curation_agent(
    *,
    project_id: UUID,
    evidence_bundle: dict[str, Any],
    brand_document: BrandDocument,
    site_architecture: SiteArchitecturePlan | None = None,
) -> AssetMap:
    context = {
        "evidence_bundle": evidence_bundle,
        "brand_document": brand_document.model_dump(mode="json"),
        "site_architecture": site_architecture.model_dump(mode="json") if site_architecture else None,
    }
    model_result = call_agent_model(
        "asset_curation",
        project_id,
        "asset_curation",
        "Select real business assets first, neutral relevant stock second, no image third.",
        context,
        AssetMap.model_json_schema(),
        temperature=0.2,
        max_tokens=4096,
        timeout_seconds=480,
    )

    def fallback() -> AssetMap:
        return AssetMap(
            review_section_visual_treatment="Simple cards with source labels.",
            stock_image_gaps=[] if evidence_bundle.get("image_asset_candidates") else ["hero"],
            rejected_assets=[],
            metadata={
                "source_image_candidates": evidence_bundle.get("image_asset_candidates") or [],
                "logo_candidates": evidence_bundle.get("logo_candidates") or [],
            },
        )

    return model_artifact_or_fallback(AssetMap, model_result, fallback)
