"""Conversion strategy agent boundary."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from chromagora_schemas.demo_factory import BrandDocument, ConversionStrategy

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback
from chromagora_workers.demo_factory.copy_quality import build_hero_body_fallback

logger = logging.getLogger(__name__)


def run_conversion_strategy_agent(
    *,
    project_id: UUID,
    brand_document: BrandDocument,
    evidence_bundle: dict[str, Any],
    framework_patterns: list[dict[str, Any]] | None = None,
) -> ConversionStrategy:
    context = {
        "brand_document": brand_document.model_dump(mode="json"),
        "evidence_bundle": evidence_bundle,
        "framework_patterns": framework_patterns or [],
    }

    def fallback() -> ConversionStrategy:
        business_name = brand_document.business_identity.get("name", "this business")
        cta = evidence_bundle.get("suggested_demo_cta") or "Request a quote"
        hero_body = build_hero_body_fallback(
            business_name=business_name,
            vertical=brand_document.vertical,
            primary_services=evidence_bundle.get("service_candidates") or [],
            service_area=", ".join(evidence_bundle.get("location_service_area_candidates") or []) or None,
            contact_path=_first_contact(evidence_bundle),
        )
        return ConversionStrategy(
            primary_visitor_intent="Understand services quickly and make contact.",
            primary_cta=cta,
            secondary_cta="See services",
            hero_message=f"A clearer, faster way to choose {business_name}",
            section_hierarchy_rationale=["Lead with service clarity", "Show proof only when verified", "Make contact easy"],
            offer_clarity_notes=["Avoid invented prices, guarantees, or availability claims"],
            proof_strategy=["Use verified reviews only", "Use visible site evidence"],
            objection_handling_notes=["Reduce uncertainty with clear service area and process"],
            service_prioritization=evidence_bundle.get("service_candidates") or ["Core services"],
            copy_blocks={
                "hero_body": hero_body,
                "cta_body": "Ready to talk through the project? Start with a quick quote request.",
            },
            claims_requiring_verification=[],
            excluded_unsupported_claims=["years in business", "licensed and insured", "24/7 emergency availability"],
        )

    try:
        model_result = call_agent_model(
            "conversion_strategy",
            project_id,
            "conversion_strategy",
            (
                "Use conversion frameworks to clarify the page strategy without inventing trust claims. "
                "Do not copy long snippets from the crawled site. "
                "Do not use scaffold phrases such as 'public evidence', 'trust signals', or 'private preview' in customer-facing copy. "
                "Write original customer-facing copy grounded in evidence. "
                "When a claim is not present in evidence, omit it."
            ),
            context,
            ConversionStrategy.model_json_schema(),
            temperature=0.25,
            max_tokens=4096,
            timeout_seconds=480,
        )
    except Exception as exc:
        logger.warning("Conversion strategy model call failed, using fallback: %s", exc)
        model_result = {}

    strategy = model_artifact_or_fallback(ConversionStrategy, model_result, fallback)
    strategy.excluded_unsupported_claims = list(
        dict.fromkeys(
            strategy.excluded_unsupported_claims
            + ["years in business", "licensed and insured", "24/7 emergency availability"]
        )
    )
    return strategy


def _first_contact(evidence_bundle: dict[str, Any]) -> str | None:
    contacts = evidence_bundle.get("contact_candidates") or {}
    phones = contacts.get("phones") or []
    if phones:
        return str(phones[0])
    emails = contacts.get("emails") or []
    if emails:
        return str(emails[0])
    return None
