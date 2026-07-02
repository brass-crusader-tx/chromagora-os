"""Deterministic QA checks for Demo Factory SiteSpecs."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from chromagora_schemas.demo_factory import SiteSpec
from chromagora_workers.demo_factory.copy_quality import BANNED_HERO_PHRASES


class DeterministicQAFailure(BaseModel):
    issue_code: str
    field: str | None = None
    severity: str = "blocking"
    detail: str = ""


class DeterministicQAResult(BaseModel):
    passed: bool
    failures: list[DeterministicQAFailure] = []
    warnings: list[DeterministicQAFailure] = []


def run_deterministic_qa(site_spec: SiteSpec, evidence_bundle: dict[str, Any] | None = None) -> DeterministicQAResult:
    """Run all deterministic QA checks against a SiteSpec."""
    failures: list[DeterministicQAFailure] = []
    warnings: list[DeterministicQAFailure] = []

    failures.extend(_check_service_area_clean(site_spec))
    failures.extend(_check_hero_copy(site_spec))
    failures.extend(_check_review_provenance(site_spec))
    failures.extend(_check_required_sections(site_spec))
    failures.extend(_check_slug_canonical(site_spec))
    warnings.extend(_check_warnings(site_spec, evidence_bundle))

    return DeterministicQAResult(
        passed=not failures,
        failures=failures,
        warnings=warnings,
    )


def _check_service_area_clean(site_spec: SiteSpec) -> list[DeterministicQAFailure]:
    failures: list[DeterministicQAFailure] = []
    service_area = site_spec.service_area
    if not service_area:
        return failures

    if len(service_area) > 120:
        failures.append(DeterministicQAFailure(
            issue_code="service_area_too_long",
            field="service_area",
            detail=f"Service area is {len(service_area)} chars, likely contaminated.",
        ))

    contamination_words = [
        "receive", "ensuring", "guarantee", "replacement", "upgrade", "quote",
        "book", "call", "property", "hydration", "services", "landscaping",
        "maintenance", "professional", "dedicated", "excellence", "quality",
    ]
    lowered = service_area.lower()
    for word in contamination_words:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            failures.append(DeterministicQAFailure(
                issue_code="service_area_contaminated",
                field="service_area",
                detail=f"Service area contains contamination word: '{word}'.",
            ))
            break

    if re.search(r"[.!?;:]", service_area):
        failures.append(DeterministicQAFailure(
            issue_code="service_area_contains_sentence",
            field="service_area",
            detail="Service area contains sentence punctuation.",
        ))

    return failures


def _check_hero_copy(site_spec: SiteSpec) -> list[DeterministicQAFailure]:
    failures: list[DeterministicQAFailure] = []
    hero_body = None
    hero_heading = None

    for page in site_spec.pages:
        for section in page.sections:
            if section.type == "hero":
                hero_body = section.body
                hero_heading = section.heading
                break

    if not hero_body:
        failures.append(DeterministicQAFailure(
            issue_code="empty_hero_body",
            field="hero_body",
            detail="Hero section has no body copy.",
        ))
        return failures

    if len(hero_body) < 40:
        failures.append(DeterministicQAFailure(
            issue_code="hero_body_too_short",
            field="hero_body",
            detail=f"Hero body is too short ({len(hero_body)} chars).",
        ))

    if len(hero_body) > 600:
        failures.append(DeterministicQAFailure(
            issue_code="hero_body_too_long",
            field="hero_body",
            detail=f"Hero body is too long ({len(hero_body)} chars).",
        ))

    lowered = hero_body.lower()
    for phrase in BANNED_HERO_PHRASES:
        if phrase in lowered:
            failures.append(DeterministicQAFailure(
                issue_code="generic_hero_phrase",
                field="hero_body",
                detail=f"Hero body contains banned generic phrase: '{phrase}'.",
            ))

    if hero_heading:
        heading_lowered = hero_heading.lower()
        for phrase in BANNED_HERO_PHRASES:
            if phrase in heading_lowered:
                failures.append(DeterministicQAFailure(
                    issue_code="generic_hero_phrase",
                    field="hero_heading",
                    detail=f"Hero heading contains banned generic phrase: '{phrase}'.",
                ))

    return failures


def _check_review_provenance(site_spec: SiteSpec) -> list[DeterministicQAFailure]:
    failures: list[DeterministicQAFailure] = []

    if not site_spec.reviews:
        return failures

    for i, review in enumerate(site_spec.reviews):
        if not review.source_url:
            failures.append(DeterministicQAFailure(
                issue_code="review_missing_source_url",
                field=f"reviews[{i}]",
                detail=f"Review at index {i} has no source_url.",
            ))
        if review.source_kind == "unknown" and review.confidence_score < 0.7:
            failures.append(DeterministicQAFailure(
                issue_code="review_low_confidence_unknown_source",
                field=f"reviews[{i}]",
                detail=f"Review at index {i} has unknown source and low confidence.",
            ))

    return failures


def _check_required_sections(site_spec: SiteSpec) -> list[DeterministicQAFailure]:
    failures: list[DeterministicQAFailure] = []

    if not site_spec.pages:
        failures.append(DeterministicQAFailure(
            issue_code="no_pages",
            detail="SiteSpec has no pages.",
        ))
        return failures

    has_hero = False
    has_contact = False
    for page in site_spec.pages:
        for section in page.sections:
            if section.type == "hero":
                has_hero = True
            if section.type == "contact_panel":
                has_contact = True

    if not has_hero:
        failures.append(DeterministicQAFailure(
            issue_code="missing_hero_section",
            detail="No hero section found.",
        ))

    if not has_contact:
        failures.append(DeterministicQAFailure(
            issue_code="missing_contact_section",
            detail="No contact section found.",
        ))

    if not site_spec.primary_cta:
        failures.append(DeterministicQAFailure(
            issue_code="missing_primary_cta",
            detail="No primary CTA configured.",
        ))

    return failures


def _check_slug_canonical(site_spec: SiteSpec) -> list[DeterministicQAFailure]:
    failures: list[DeterministicQAFailure] = []
    metadata_slug = (site_spec.metadata or {}).get("demo_slug", "")
    if metadata_slug and " " in metadata_slug:
        failures.append(DeterministicQAFailure(
            issue_code="slug_not_canonical",
            field="metadata.demo_slug",
            detail=f"Slug '{metadata_slug}' contains spaces.",
        ))
    return failures


def _check_warnings(site_spec: SiteSpec, evidence_bundle: dict[str, Any] | None) -> list[DeterministicQAFailure]:
    warnings: list[DeterministicQAFailure] = []

    if not site_spec.reviews:
        warnings.append(DeterministicQAFailure(
            issue_code="no_reviews",
            severity="warning",
            detail="No reviews included in SiteSpec.",
        ))

    if evidence_bundle:
        service_area = site_spec.service_area or ""
        if service_area and len(service_area) > 60:
            warnings.append(DeterministicQAFailure(
                issue_code="service_area_long",
                severity="warning",
                detail=f"Service area is {len(service_area)} chars, review for cleanliness.",
            ))

    return warnings
