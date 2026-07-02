"""Brand synthesis agent boundary."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from chromagora_schemas.demo_factory import BrandDocument

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback


def run_brand_synthesis_agent(*, project_id: UUID, evidence_bundle: dict[str, Any]) -> BrandDocument:
    model_result = call_agent_model(
        "brand_synthesis",
        project_id,
        "brand_synthesis",
        "Create a grounded BrandDocument from one business evidence bundle.",
        evidence_bundle,
        BrandDocument.model_json_schema(),
        temperature=0.2,
        max_tokens=4096,
        timeout_seconds=420,
    )

    def fallback() -> BrandDocument:
        business_name = evidence_bundle.get("business_name") or "Local Business"
        colors = evidence_bundle.get("colors_logo_candidates") or ["#1f2937", "#2563eb", "#f8fafc"]
        contacts = evidence_bundle.get("contact_candidates") or {}
        phones = contacts.get("phones") or []
        emails = contacts.get("emails") or []
        return BrandDocument(
            business_identity={"name": business_name, "domain": evidence_bundle.get("source_domain")},
            vertical=(evidence_bundle.get("service_candidates") or ["Local Services"])[0],
            location_service_area_signals=evidence_bundle.get("location_service_area_candidates") or [],
            phone_email_contact_signals={
                "phone": phones[0] if phones else None,
                "email": emails[0] if emails else None,
            },
            visual_identity={"colors": colors, "logo_candidates": evidence_bundle.get("logo_candidates") or []},
            primary_hex=colors[0],
            secondary_hex=colors[2] if len(colors) > 2 else "#f8fafc",
            accent_hex=colors[1] if len(colors) > 1 else "#2563eb",
            brand_truths_to_preserve=[business_name],
            execution_flaws_not_to_preserve=[note for note in [evidence_bundle.get("old_site_weakness_notes")] if note],
            voice_guidance="Clear, specific, and local-service focused.",
            freedom_level="medium",
            evidence_references=["csv", "homepage"],
        )

    return model_artifact_or_fallback(BrandDocument, model_result, fallback)
