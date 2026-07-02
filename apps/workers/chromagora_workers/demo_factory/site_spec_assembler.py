"""Assemble renderer-safe SiteSpec artifacts."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from chromagora_schemas.demo_factory import (
    AssetMap,
    BeforeAfterRevealConfig,
    BrandConfig,
    BrandDocument,
    CTAConfig,
    ChromagoraFooterConfig,
    ConversionStrategy,
    NavigationItem,
    ReviewEvidenceBlock,
    SiteArchitecturePlan,
    SitePageSpec,
    SiteSectionSpec,
    SiteSpec,
)
from chromagora_workers.demo_factory.copy_quality import (
    business_specific_heading,
    cta_from_contact_and_vertical,
    remove_ai_slop_phrases,
    service_items_from_evidence,
)


def assemble_site_spec(
    *,
    sb,
    tenant_id: UUID,
    project: dict[str, Any],
    brand_document: BrandDocument,
    conversion_strategy: ConversionStrategy,
    site_architecture: SiteArchitecturePlan,
    asset_map: AssetMap,
    review_evidence: ReviewEvidenceBlock,
    evidence_bundle: dict[str, Any],
) -> tuple[SiteSpec, dict[str, Any]]:
    project_id = UUID(str(project["id"]))
    old_screenshot_urls = _old_screenshot_urls(sb, project_id)
    old_screenshot_url = (
        evidence_bundle.get("old_site_screenshot_url")
        or old_screenshot_urls.get("desktop")
        or old_screenshot_urls.get("mobile")
        or old_screenshot_urls.get("fallback")
    )
    business_name = project.get("business_name") or "Local Business"
    service_area = ", ".join(evidence_bundle.get("location_service_area_candidates") or []) or None
    vertical = brand_document.vertical or "Local Services"
    service_items = _service_items(conversion_strategy, evidence_bundle, vertical)
    primary_cta = _primary_cta(conversion_strategy, evidence_bundle, vertical)
    hero_heading = business_specific_heading(
        business_name=business_name,
        vertical=vertical,
        service_area=service_area,
        current_heading=conversion_strategy.hero_message,
    )

    section_library: dict[str, SiteSectionSpec] = {
        "hero": SiteSectionSpec(
            type="hero",
            section_id="hero",
            variant="split_visual" if old_screenshot_url else "centered",
            eyebrow=business_name,
            heading=hero_heading,
            body=remove_ai_slop_phrases(conversion_strategy.copy_blocks.get("hero_body"))
            or "A cleaner private preview that makes the next step easier to find on mobile.",
            cta=primary_cta,
            props={"service_area": evidence_bundle.get("location_service_area_candidates") or []},
        ),
        "service_grid": SiteSectionSpec(
            type="service_grid",
            section_id="services",
            variant="cards",
            heading=f"{business_name} services, easier to scan",
            body="The rebuilt layout keeps services close to the quote path instead of burying them in generic page copy.",
            items=service_items,
        ),
        "trust_strip": SiteSectionSpec(
            type="trust_strip",
            section_id="trust",
            variant="text_proof",
            heading="Grounded in the business people already find online",
            items=[
                {"label": "Real business identity", "value": project.get("business_name")},
                {"label": "No invented offers", "value": "Verified claims only"},
                {"label": "Mobile-first contact path", "value": conversion_strategy.primary_cta},
            ],
        ),
        "gallery_grid": SiteSectionSpec(
            type="gallery_grid",
            section_id="gallery",
            variant="cards",
            heading="Work and service visuals",
            items=[
                {"url": url, "alt": f"{project.get('business_name')} service image"}
                for url in (evidence_bundle.get("image_asset_candidates") or [])[:6]
            ],
        ),
        "review_cards": SiteSectionSpec(
            type="review_cards",
            section_id="reviews",
            variant="cards",
            heading="What customers say",
            items=[review.model_dump(mode="json") for review in review_evidence.selected_reviews],
        ),
        "process_steps": SiteSectionSpec(
            type="process_steps",
            section_id="process",
            variant="compact_rows",
            heading="Simple next steps",
            items=[
                {"title": "Tell us what you need", "body": "The page makes the request path clear on desktop and mobile."},
                {"title": "Confirm the details", "body": "Visitors can understand service fit before reaching out."},
                {"title": "Move the job forward", "body": "The call to action stays focused on the next practical step."},
            ],
        ),
        "service_area": SiteSectionSpec(
            type="service_area",
            section_id="service-area",
            heading="Service area",
            body=", ".join(evidence_bundle.get("location_service_area_candidates") or []),
        ),
        "quote_cta": SiteSectionSpec(
            type="quote_cta",
            section_id="quote",
            variant="simple_band",
            heading=primary_cta.label,
            body=remove_ai_slop_phrases(conversion_strategy.copy_blocks.get("cta_body"))
            or "The page keeps the request path visible so a visitor can act without digging.",
            cta=primary_cta,
        ),
        "contact_panel": SiteSectionSpec(
            type="contact_panel",
            section_id="contact",
            variant="form_first",
            heading=primary_cta.label,
            body="Share a few details and make the first conversation easier to start.",
            cta=primary_cta,
        ),
        "footer_spacer": SiteSectionSpec(type="footer_spacer", section_id="footer-spacer"),
    }

    requested_order = site_architecture.section_order_by_page.get("/") or [
        "hero",
        "service_grid",
        "trust_strip",
        "gallery_grid",
        "review_cards",
        "process_steps",
        "service_area",
        "quote_cta",
        "contact_panel",
    ]
    sections: list[SiteSectionSpec] = []
    for section_type in requested_order:
        if section_type == "review_cards" and (review_evidence.omit_review_section or not review_evidence.selected_reviews):
            continue
        if section_type == "gallery_grid" and not evidence_bundle.get("image_asset_candidates"):
            continue
        if section_type == "service_area" and not evidence_bundle.get("location_service_area_candidates"):
            continue
        section = section_library.get(section_type)
        if section:
            sections.append(section)
    if not any(section.type == "contact_panel" for section in sections):
        sections.append(section_library["contact_panel"])

    page = SitePageSpec(
        slug="/",
        title=project.get("business_name") or "Demo Site",
        description=f"Private Chromagora demo for {project.get('business_name')}",
        sections=sections,
    )
    spec = SiteSpec(
        project_id=project_id,
        business_name=business_name,
        business_vertical=vertical,
        service_area=service_area,
        brand=BrandConfig(
            primary_hex=brand_document.primary_hex or "#1f2937",
            secondary_hex=brand_document.secondary_hex or "#f8fafc",
            accent_hex=brand_document.accent_hex or "#2563eb",
            logo_asset_id=brand_document.logo_asset_id,
            tone=brand_document.voice_guidance,
        ),
        pages=[page],
        navigation=[NavigationItem(**item) for item in site_architecture.navigation],
        primary_cta=primary_cta,
        sticky_mobile_cta=primary_cta,
        assets=[],
        reviews=[] if review_evidence.omit_review_section else review_evidence.selected_reviews,
        trust_claims=_supported_trust_claims(brand_document, conversion_strategy),
        forms=[{"id": "quote", "kind": "contact_request", "verified": primary_cta.kind in {"phone", "email"}}],
        before_after_reveal=BeforeAfterRevealConfig(
            enabled=bool(old_screenshot_url),
            orientation="horizontal",
            before_image_url=old_screenshot_url,
            before_desktop_image_url=old_screenshot_urls.get("desktop") or old_screenshot_url,
            before_mobile_image_url=old_screenshot_urls.get("mobile") or old_screenshot_url,
            instruction_text=evidence_bundle.get("before_after_slider_angle") or "Slide to reveal the rebuilt version",
        ),
        chromagora_footer=ChromagoraFooterConfig(),
        metadata={
            "asset_map": asset_map.model_dump(mode="json"),
            "conversion_strategy": conversion_strategy.model_dump(mode="json"),
            "site_architecture": site_architecture.model_dump(mode="json"),
            "review_evidence": review_evidence.model_dump(mode="json"),
        },
    )

    spec_row = {
        "id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "project_id": str(project_id),
        "status": "draft",
        "spec_json": spec.model_dump(mode="json"),
        "version": 1,
        "is_current": False,
    }
    sb.table("demo_site_specs").insert(spec_row).execute()
    return spec, spec_row


def _service_items(
    conversion_strategy: ConversionStrategy,
    evidence_bundle: dict[str, Any],
    vertical: str | None,
) -> list[dict[str, Any]]:
    services = conversion_strategy.service_prioritization or evidence_bundle.get("service_candidates") or ["Core services"]
    return service_items_from_evidence(services=services, vertical=vertical)


def _primary_cta(conversion_strategy: ConversionStrategy, evidence_bundle: dict[str, Any], vertical: str | None) -> CTAConfig:
    contacts = evidence_bundle.get("contact_candidates") or {}
    phones = contacts.get("phones") or []
    emails = contacts.get("emails") or []
    label = cta_from_contact_and_vertical(
        current_label=conversion_strategy.primary_cta,
        suggested_label=evidence_bundle.get("suggested_demo_cta"),
        vertical=vertical,
    )
    if phones:
        normalized_phone = "".join(char for char in str(phones[0]) if char.isdigit() or char == "+")
        return CTAConfig(label=label, href=f"tel:{normalized_phone}", kind="phone")
    if emails:
        return CTAConfig(label=label, href=f"mailto:{emails[0]}", kind="email")
    return CTAConfig(label=label, href="#contact", kind="form")


def _supported_trust_claims(brand_document: BrandDocument, conversion_strategy: ConversionStrategy) -> list[str]:
    unsupported = {claim.lower() for claim in conversion_strategy.excluded_unsupported_claims}
    claims: list[str] = []
    for claim in brand_document.brand_truths_to_preserve:
        lowered = claim.lower()
        if not any(blocked in lowered for blocked in unsupported):
            claims.append(claim)
    return claims[:6]


def _old_screenshot_urls(sb, project_id: UUID) -> dict[str, str | None]:
    resp = (
        sb.table("demo_site_assets")
        .select("*")
        .eq("project_id", str(project_id))
        .eq("asset_type", "old_site_screenshot")
        .execute()
    )
    urls: dict[str, str | None] = {"desktop": None, "mobile": None, "fallback": None}
    for asset in resp.data or []:
        url = _asset_public_url(asset)
        if not url:
            continue
        viewport = (asset.get("metadata_json") or {}).get("viewport")
        if viewport in {"desktop", "mobile"} and not urls[viewport]:
            urls[viewport] = url
        if not urls["fallback"]:
            urls["fallback"] = url
    return urls


def _asset_public_url(asset: dict[str, Any]) -> str | None:
    if asset.get("public_url"):
        return asset["public_url"]
    if asset.get("storage_bucket") and asset.get("storage_path"):
        return f"/api/storage/{asset['storage_bucket']}/{asset['storage_path']}"
    return None
