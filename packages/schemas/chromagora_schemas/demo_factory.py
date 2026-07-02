"""Shared Demo Factory schemas.

Agents in the Demo Factory vertical exchange structured artifacts. The public
renderer consumes only ``SiteSpec``; arbitrary React, CSS, or HTML are not part
of the primary output path.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


BatchStatus = Literal["queued", "running", "paused", "completed", "failed", "cancelled"]
RowStatus = Literal[
    "queued",
    "running",
    "published",
    "failed_retryable",
    "failed_terminal",
    "skipped",
    "paused",
]
ProjectStatus = Literal[
    "queued",
    "crawling",
    "brand_synthesis",
    "copy_strategy",
    "site_architecture",
    "asset_curation",
    "review_evidence",
    "site_spec",
    "rendering",
    "qa",
    "publishing",
    "published",
    "failed_retryable",
    "failed_terminal",
    "archived",
    "waiting_rate_limit",
]
DeploymentStatus = Literal["pending", "published", "failed", "archived"]
SectionType = Literal[
    "hero",
    "service_grid",
    "trust_strip",
    "gallery_grid",
    "review_cards",
    "process_steps",
    "service_area",
    "quote_cta",
    "contact_panel",
    "footer_spacer",
]


class DemoBatchCreate(BaseModel):
    source_filename: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DemoBatchRow(BaseModel):
    id: UUID | None = None
    batch_id: UUID | None = None
    project_id: UUID | None = None
    row_number: int = Field(ge=1)
    rank: float | None = None
    business_name: str
    website_url: str | None = None
    website_domain: str | None = None
    demo_slug: str
    raw_row_json: dict[str, Any] = Field(default_factory=dict)
    status: RowStatus = "queued"
    attempt_count: int = Field(default=0, ge=0)
    last_error: str | None = None


class DemoSiteProject(BaseModel):
    id: UUID | None = None
    tenant_id: UUID | None = None
    business_id: UUID | None = None
    batch_id: UUID | None = None
    batch_row_id: UUID | None = None
    source_domain: str | None = None
    normalized_domain: str | None = None
    source_url: str | None = None
    business_name: str
    demo_slug: str
    demo_host: str | None = None
    status: ProjectStatus = "queued"
    current_stage: str | None = None
    verify_before_build: bool = True
    priority_score: float | None = None
    input_row_json: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    error_message: str | None = None


class DemoSourceSnapshot(BaseModel):
    id: UUID | None = None
    project_id: UUID
    source_url: str
    final_url: str | None = None
    page_type: str | None = None
    http_status: int | None = None
    title: str | None = None
    meta_description: str | None = None
    visible_text: str | None = None
    text_summary: str | None = None
    screenshot_bucket: str | None = None
    screenshot_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DemoAsset(BaseModel):
    id: UUID | None = None
    project_id: UUID
    snapshot_id: UUID | None = None
    asset_type: str
    source_url: str | None = None
    storage_bucket: str | None = None
    storage_path: str | None = None
    public_url: str | None = None
    alt_text: str | None = None
    width: int | None = None
    height: int | None = None
    status: Literal["candidate", "selected", "rejected", "published"] = "candidate"
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrandDocument(BaseModel):
    business_identity: dict[str, Any]
    vertical: str | None = None
    location_service_area_signals: list[str] = Field(default_factory=list)
    phone_email_contact_signals: dict[str, str | None] = Field(default_factory=dict)
    visual_identity: dict[str, Any] = Field(default_factory=dict)
    primary_hex: str | None = None
    secondary_hex: str | None = None
    accent_hex: str | None = None
    logo_asset_id: UUID | None = None
    real_brand_assets_to_reuse: list[str] = Field(default_factory=list)
    brand_truths_to_preserve: list[str] = Field(default_factory=list)
    execution_flaws_not_to_preserve: list[str] = Field(default_factory=list)
    voice_guidance: str | None = None
    freedom_level: Literal["low", "medium", "high"] = "medium"
    evidence_references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversionStrategy(BaseModel):
    primary_visitor_intent: str
    primary_cta: str
    secondary_cta: str | None = None
    hero_message: str
    section_hierarchy_rationale: list[str] = Field(default_factory=list)
    offer_clarity_notes: list[str] = Field(default_factory=list)
    proof_strategy: list[str] = Field(default_factory=list)
    objection_handling_notes: list[str] = Field(default_factory=list)
    service_prioritization: list[str] = Field(default_factory=list)
    copy_blocks: dict[str, str] = Field(default_factory=dict)
    claims_requiring_verification: list[str] = Field(default_factory=list)
    excluded_unsupported_claims: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SiteArchitecturePlan(BaseModel):
    pages: list[dict[str, Any]]
    navigation: list[dict[str, str]] = Field(default_factory=list)
    section_order_by_page: dict[str, list[SectionType]] = Field(default_factory=dict)
    mobile_cta_strategy: str | None = None
    omitted_sections: list[SectionType] = Field(default_factory=list)
    high_signal_optional_sections: list[SectionType] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class AssetMap(BaseModel):
    hero_asset_id: UUID | None = None
    logo_asset_id: UUID | None = None
    service_section_assets: dict[str, UUID | str] = Field(default_factory=dict)
    gallery_project_assets: list[UUID | str] = Field(default_factory=list)
    review_section_visual_treatment: str | None = None
    stock_image_gaps: list[str] = Field(default_factory=list)
    rejected_assets: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewEvidence(BaseModel):
    reviewer_name: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    review_text: str
    review_date: date | None = None
    source_url: str
    identity_match_signals: dict[str, bool] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=1)


class ReviewEvidenceBlock(BaseModel):
    selected_reviews: list[ReviewEvidence] = Field(default_factory=list, max_length=5)
    rejected_reviews: list[dict[str, Any]] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    identity_match_signals: dict[str, bool] = Field(default_factory=dict)
    confidence_score: float = Field(default=0, ge=0, le=1)
    omit_review_section: bool = True

    @field_validator("omit_review_section")
    @classmethod
    def omit_when_low_confidence(cls, value: bool, info):
        data = info.data
        if data.get("confidence_score", 0) < 0.65:
            return True
        return value


class CTAConfig(BaseModel):
    label: str
    href: str
    kind: Literal["phone", "email", "form", "internal", "external"] = "form"
    aria_label: str | None = None


class ChromagoraFooterConfig(BaseModel):
    enabled: bool = True
    text: str = "Created at Chromagora by human minds"
    logo_url: str | None = None
    link_url: str = "https://chromagora.com"


class BeforeAfterRevealConfig(BaseModel):
    enabled: bool = False
    orientation: Literal["horizontal", "vertical"] = "horizontal"
    before_image_url: str | None = None
    before_mobile_image_url: str | None = None
    before_desktop_image_url: str | None = None
    instruction_text: str = "Slide to reveal the rebuilt version"
    default_reveal_percent: int = Field(default=45, ge=0, le=100)


class BrandConfig(BaseModel):
    primary_hex: str = "#1f2937"
    secondary_hex: str = "#f8fafc"
    accent_hex: str = "#2563eb"
    logo_asset_id: UUID | None = None
    logo_url: str | None = None
    font_family: str | None = None
    tone: str | None = None


class NavigationItem(BaseModel):
    label: str
    href: str


class AssetReference(BaseModel):
    id: UUID | None = None
    asset_type: str
    url: str | None = None
    alt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SiteSectionSpec(BaseModel):
    type: SectionType
    section_id: str
    variant: str | None = None
    heading: str | None = None
    eyebrow: str | None = None
    body: str | None = None
    cta: CTAConfig | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    asset_ids: list[UUID] = Field(default_factory=list)
    props: dict[str, Any] = Field(default_factory=dict)


class SitePageSpec(BaseModel):
    slug: str = "/"
    title: str
    description: str | None = None
    sections: list[SiteSectionSpec] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def page_slug_starts_with_slash(cls, value: str) -> str:
        if not value.startswith("/"):
            return f"/{value}"
        return value


class SiteSpec(BaseModel):
    project_id: UUID
    business_name: str
    business_vertical: str
    service_area: str | None = None
    brand: BrandConfig
    pages: list[SitePageSpec] = Field(min_length=1)
    navigation: list[NavigationItem] = Field(default_factory=list)
    primary_cta: CTAConfig
    sticky_mobile_cta: CTAConfig | None = None
    assets: list[AssetReference] = Field(default_factory=list)
    reviews: list[ReviewEvidence] = Field(default_factory=list, max_length=5)
    trust_claims: list[str] = Field(default_factory=list)
    forms: list[dict[str, Any]] = Field(default_factory=list)
    before_after_reveal: BeforeAfterRevealConfig = Field(default_factory=BeforeAfterRevealConfig)
    chromagora_footer: ChromagoraFooterConfig = Field(default_factory=ChromagoraFooterConfig)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QAReport(BaseModel):
    project_id: UUID
    spec_id: UUID | None = None
    status: Literal["pending", "passed", "failed", "warning"]
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    screenshots: list[dict[str, Any]] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)


class AdversarialOwnerReactionReport(BaseModel):
    project_id: UUID
    passed: bool
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
    owner_reaction_risk_score: float = Field(ge=0, le=1)


class DemoDeployment(BaseModel):
    id: UUID | None = None
    project_id: UUID
    spec_id: UUID | None = None
    demo_slug: str
    demo_host: str
    demo_url: str
    status: DeploymentStatus = "pending"
    published_at: datetime | None = None
    verified_at: datetime | None = None
    error_message: str | None = None


class DemoModelCall(BaseModel):
    id: UUID | None = None
    project_id: UUID
    batch_id: UUID | None = None
    agent_run_id: UUID | None = None
    agent_name: str
    stage: str
    model: str
    request_hash: str
    input_token_estimate: int | None = None
    output_token_estimate: int | None = None
    status: Literal["running", "succeeded", "failed", "rate_limited"] = "running"
    http_status: int | None = None
    error_code: str | None = None
    latency_ms: int | None = None
    attempt_number: int = 1
    error_message: str | None = None


class SupervisorEvent(BaseModel):
    id: UUID | None = None
    project_id: UUID | None = None
    batch_id: UUID | None = None
    event_type: str
    severity: Literal["info", "warning", "error"] = "info"
    stage: str | None = None
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


def score_review_identity_match(signals: dict[str, bool]) -> float:
    """Score exact-business review confidence from normalized match signals."""
    weights = {
        "business_name_match": 0.30,
        "phone_match": 0.25,
        "website_match": 0.20,
        "location_service_area_match": 0.15,
        "category_match": 0.10,
    }
    return min(1.0, sum(weight for key, weight in weights.items() if signals.get(key)))
