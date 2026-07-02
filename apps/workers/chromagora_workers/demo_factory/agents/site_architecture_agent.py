"""Site architecture agent boundary."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from chromagora_schemas.demo_factory import AssetMap, ConversionStrategy, ReviewEvidenceBlock, SiteArchitecturePlan

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback


def run_site_architecture_agent(
    *,
    project_id: UUID,
    conversion_strategy: ConversionStrategy,
    asset_map: AssetMap | None = None,
    review_evidence: ReviewEvidenceBlock | None = None,
    demo_angle: str | None = None,
) -> SiteArchitecturePlan:
    context: dict[str, Any] = {
        "conversion_strategy": conversion_strategy.model_dump(mode="json"),
        "asset_map": asset_map.model_dump(mode="json") if asset_map else None,
        "review_evidence": review_evidence.model_dump(mode="json") if review_evidence else None,
        "demo_angle": demo_angle,
    }
    model_result = call_agent_model(
        "site_architecture",
        project_id,
        "site_architecture",
        "Choose from controlled SiteSpec section types only.",
        context,
        SiteArchitecturePlan.model_json_schema(),
        temperature=0.2,
        max_tokens=4096,
        timeout_seconds=360,
    )

    def fallback() -> SiteArchitecturePlan:
        sections = ["hero", "service_grid", "trust_strip", "quote_cta", "contact_panel"]
        if review_evidence and not review_evidence.omit_review_section:
            sections.insert(3, "review_cards")
        return SiteArchitecturePlan(
            pages=[{"slug": "/", "title": "Home"}],
            navigation=[{"label": "Services", "href": "#services"}, {"label": "Contact", "href": "#contact"}],
            section_order_by_page={"/": sections},
            mobile_cta_strategy="Sticky primary CTA on mobile.",
            omitted_sections=[],
            high_signal_optional_sections=["gallery_grid", "review_cards"],
            rationale=["One focused landing page is the v0.1 default."],
        )

    return model_artifact_or_fallback(SiteArchitecturePlan, model_result, fallback)
