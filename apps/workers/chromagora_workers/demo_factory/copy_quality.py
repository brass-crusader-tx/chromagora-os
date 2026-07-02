"""Copy-quality helpers for deterministic Demo Factory assembly."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


BANNED_SLOP_PHRASES = [
    "solutions tailored to your needs",
    "dedicated to excellence",
    "trusted professionals",
    "quality you can count on",
    "contact us today",
    "we pride ourselves",
    "comprehensive services",
    "a focused demo page",
    "public evidence",
    "trust signals",
    "private preview",
    "built around the services",
]

BANNED_HERO_PHRASES = [
    "a focused demo page",
    "public evidence",
    "trust signals",
    "private preview",
    "built around the services",
    "contact path visible from",
    "solutions tailored",
    "dedicated to excellence",
]

CTA_DEFAULTS_BY_VERTICAL = {
    "roofing": "Text a photo of your roof",
    "concrete": "Request a concrete estimate",
    "excavation": "Talk through the job site",
    "plumbing": "Request a plumbing callback",
    "hvac": "Book a service call",
    "landscaping": "Request a yard quote",
    "junk removal": "Send photos for a pickup estimate",
    "tree service": "Request a tree work estimate",
    "painting": "Request a painting estimate",
    "remodeling": "Talk through the project",
}

VERTICAL_SERVICE_DEFAULTS = {
    "roofing": ["Roof repairs", "Roof replacement", "Roof inspections"],
    "concrete": ["Driveways", "Walkways", "Slabs"],
    "landscaping": ["Lawn care", "Garden work", "Hardscaping"],
    "plumbing": ["Plumbing repairs", "Fixture work", "Service callbacks"],
    "hvac": ["Service calls", "System repairs", "Maintenance"],
    "junk removal": ["Pickup estimates", "Cleanouts", "Item removal"],
    "tree service": ["Tree trimming", "Tree removal", "Site cleanup"],
}


def remove_ai_slop_phrases(text: str | None) -> str | None:
    if not text:
        return text
    cleaned = text
    for phrase in BANNED_SLOP_PHRASES:
        cleaned = cleaned.replace(phrase, "").replace(phrase.title(), "")
    return " ".join(cleaned.split()).strip() or None


def normalized_vertical(value: str | None) -> str:
    text = (value or "local services").strip().lower()
    for key in CTA_DEFAULTS_BY_VERTICAL:
        if key in text:
            return key
    return text


def business_specific_heading(
    *,
    business_name: str | None,
    vertical: str | None,
    service_area: str | None,
    current_heading: str | None = None,
) -> str:
    cleaned = remove_ai_slop_phrases(current_heading)
    if cleaned and not _looks_generic(cleaned):
        return cleaned
    vertical_key = normalized_vertical(vertical)
    area = f" in {service_area}" if service_area else ""
    if vertical_key == "roofing":
        return f"Roof repairs and replacement estimates made easier{area}"
    if vertical_key == "landscaping":
        return f"Landscaping quotes made easier to request{area}"
    if vertical_key == "plumbing":
        return f"Plumbing callbacks made easier to book{area}"
    if vertical_key == "hvac":
        return f"Service calls made easier to book{area}"
    if vertical_key == "concrete":
        return f"Concrete estimates made easier to request{area}"
    label = vertical.title() if vertical else "Service"
    return f"{label} requests made easier{area}"


def cta_from_contact_and_vertical(
    *,
    current_label: str | None,
    suggested_label: str | None,
    vertical: str | None,
) -> str:
    for label in [suggested_label, current_label]:
        cleaned = remove_ai_slop_phrases(label)
        if cleaned and cleaned.lower() not in {"request a quote", "contact us", "get started"}:
            return cleaned
    return CTA_DEFAULTS_BY_VERTICAL.get(normalized_vertical(vertical), "Request an estimate")


def service_items_from_evidence(
    *,
    services: list[str],
    vertical: str | None,
) -> list[dict[str, Any]]:
    service_names = [remove_ai_slop_phrases(service) or service for service in services if service]
    inferred = False
    if not service_names or service_names == ["Core services"]:
        service_names = VERTICAL_SERVICE_DEFAULTS.get(normalized_vertical(vertical), ["Main services"])
        inferred = True
    return [
        {
            "title": service,
            "body": service_body_from_evidence(service),
            "metadata": {"inferred": inferred, "source": "vertical_default" if inferred else "evidence"},
        }
        for service in service_names[:6]
    ]


def service_body_from_evidence(service: str) -> str:
    label = service.lower()
    if "roof" in label:
        return "Make roof needs easier to describe and estimate from the first click."
    if "landscap" in label or "lawn" in label or "yard" in label:
        return "Help visitors explain the outdoor work they want done without hunting through the page."
    if "plumb" in label:
        return "Keep the callback path obvious for repair and service requests."
    if "concrete" in label or "driveway" in label or "slab" in label:
        return "Give visitors a clearer way to start an estimate for the project."
    return "A clearer service block helps visitors understand fit before they reach out."


def _looks_generic(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in BANNED_SLOP_PHRASES) or lowered.startswith("professional ")


def build_hero_body_fallback(
    business_name: str,
    vertical: str | None,
    primary_services: list[str],
    service_area: str | None,
    contact_path: str | None,
) -> str:
    """Build a deterministic hero body when the model fails."""
    name = business_name or "this business"
    area = f"{service_area}-area" if service_area else "local"
    vertical_label = (vertical or "services").strip()
    service_hint = ""
    if primary_services:
        top = primary_services[0]
        if top:
            service_hint = f" around {top.lower()}" if len(primary_services) == 1 else ""
    contact_hint = ""
    if contact_path:
        if "tel:" in contact_path.lower():
            contact_hint = " with a quick call"
        elif "mailto:" in contact_path.lower():
            contact_hint = " by email"
        else:
            contact_hint = " online"
    return (
        f"{name} helps {area} homeowners with{service_hint} {vertical_label}"
        f"{contact_hint} through a clear, direct path."
    )


class CopyQualityIssue(BaseModel):
    issue_code: str
    field: str | None = None
    severity: str = "blocking"
    detail: str = ""


def validate_generated_copy(
    hero_body: str | None,
    hero_heading: str | None,
    service_area: str | None,
    evidence_bundle: dict[str, Any] | None = None,
) -> list[CopyQualityIssue]:
    """Validate generated copy for publishability."""
    issues: list[CopyQualityIssue] = []
    body = (hero_body or "").strip()
    heading = (hero_heading or "").strip()

    if not body:
        issues.append(CopyQualityIssue(
            issue_code="empty_hero_body",
            field="hero_body",
            detail="Hero body is empty.",
        ))
        return issues

    if len(body) < 40:
        issues.append(CopyQualityIssue(
            issue_code="hero_body_too_short",
            field="hero_body",
            detail=f"Hero body is too short ({len(body)} chars).",
        ))

    if len(body) > 600:
        issues.append(CopyQualityIssue(
            issue_code="hero_body_too_long",
            field="hero_body",
            detail=f"Hero body is too long ({len(body)} chars).",
        ))

    lowered = body.lower()
    for phrase in BANNED_HERO_PHRASES:
        if phrase in lowered:
            issues.append(CopyQualityIssue(
                issue_code="generic_hero_phrase",
                field="hero_body",
                detail=f"Contains banned generic phrase: '{phrase}'.",
            ))

    if heading:
        heading_lowered = heading.lower()
        for phrase in BANNED_HERO_PHRASES:
            if phrase in heading_lowered:
                issues.append(CopyQualityIssue(
                    issue_code="generic_hero_phrase",
                    field="hero_heading",
                    detail=f"Heading contains banned generic phrase: '{phrase}'.",
                ))

    if service_area and len(service_area) > 80:
        issues.append(CopyQualityIssue(
            issue_code="service_area_contaminated",
            field="service_area",
            detail=f"Service area is too long ({len(service_area)} chars), possible contamination.",
        ))

    if _has_raw_scrape_leakage(body, evidence_bundle):
        issues.append(CopyQualityIssue(
            issue_code="raw_scrape_leakage",
            field="hero_body",
            detail="Hero body contains a long raw snippet from the crawled site.",
        ))

    return issues


def _has_raw_scrape_leakage(text: str, evidence_bundle: dict[str, Any] | None) -> bool:
    if not evidence_bundle:
        return False
    summaries = evidence_bundle.get("crawl_text_summaries") or []
    text_lowered = text.lower()
    for summary in summaries:
        if not summary or len(summary) < 50:
            continue
        summary_lowered = summary.lower()
        if len(text_lowered) < 30:
            continue
        if summary_lowered[:60] in text_lowered:
            return True
        overlap_count = sum(1 for word in summary_lowered.split() if word in text_lowered)
        if overlap_count > 10 and overlap_count > len(summary_lowered.split()) * 0.5:
            return True
    return False
