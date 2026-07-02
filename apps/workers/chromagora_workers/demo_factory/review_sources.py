"""Grounded review/testimonial sourcing for Demo Factory."""

from __future__ import annotations

import html
import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

from chromagora_schemas.demo_factory import ReviewEvidence, ReviewEvidenceBlock, score_review_identity_match

from chromagora_workers.demo_factory.google_maps_reviews import find_google_maps_reviews


def build_grounded_review_evidence(evidence_bundle: dict[str, Any]) -> ReviewEvidenceBlock:
    """Build review evidence from deterministic sources before model validation."""
    source_domain = (evidence_bundle.get("source_domain") or "").lower().strip()
    candidates = [
        candidate
        for candidate in evidence_bundle.get("review_source_candidates") or []
        if isinstance(candidate, dict)
    ]
    if not candidates:
        candidates.extend(find_google_maps_reviews(evidence_bundle))

    selected: list[ReviewEvidence] = []
    rejected: list[dict[str, Any]] = []
    for candidate in candidates:
        rejection = _reject_candidate(candidate, source_domain)
        if rejection:
            rejected.append({**candidate, "rejected_reason": rejection})
            continue
        review = _candidate_to_review(candidate)
        if review is None:
            rejected.append({**candidate, "rejected_reason": "invalid_review_candidate"})
            continue
        if review.confidence_score < 0.65:
            rejected.append({**candidate, "rejected_reason": "low_identity_confidence"})
            continue
        selected.append(review)
        if len(selected) >= 5:
            break

    signals = _combined_signals(selected)
    confidence = max([review.confidence_score for review in selected], default=0)
    return ReviewEvidenceBlock(
        selected_reviews=selected,
        rejected_reviews=rejected[:20],
        source_urls=_unique([review.source_url for review in selected]),
        identity_match_signals=signals,
        confidence_score=confidence,
        omit_review_section=not selected,
    )


def _reject_candidate(candidate: dict[str, Any], source_domain: str) -> str | None:
    """Reject a review candidate deterministically. Returns rejection reason or None."""
    review_text = str(candidate.get("review_text") or "").strip()
    source_url = str(candidate.get("source_url") or "").strip()
    source_name = str(candidate.get("source_name") or "").strip()
    source_kind = str(candidate.get("source_kind") or candidate.get("provenance") or "").strip()
    signals = candidate.get("identity_match_signals") or {}

    if not review_text:
        return "empty_text"
    if len(review_text) < 25:
        return "text_too_short"
    if len(review_text) > 700:
        return "text_too_long"

    lower_text = review_text.lower()
    if any(token in lower_text for token in ["lorem ipsum", "{{", "}}", "as an ai", "todo", "fixme"]):
        return "looks_like_marketing_copy"

    if _is_business_description(review_text):
        return "business_description_not_review"

    marketing_patterns = [
        r"\bbook\s+now\b",
        r"\bcall\s+us\s+today\b",
        r"\brequest\s+a\s+quote\b",
        r"\bcontact\s+us\b",
        r"\bget\s+started\b",
        r"\blearn\s+more\b",
        r"\bread\s+more\b",
    ]
    if any(re.search(pattern, lower_text) for pattern in marketing_patterns) and len(review_text) < 80:
        return "looks_like_marketing_copy"

    if source_kind == "business_site":
        if not source_url:
            return "missing_identity_signal"
        candidate_domain = _extract_domain(source_url)
        if not candidate_domain:
            return "missing_identity_signal"
        source_domain_clean = source_domain.lstrip("www.")
        candidate_domain_clean = candidate_domain.lstrip("www.")
        if source_domain_clean != candidate_domain_clean:
            if source_domain_clean not in candidate_domain_clean and candidate_domain_clean not in source_domain_clean:
                return "wrong_domain"
        has_website = signals.get("website_match") is True
        has_name = signals.get("business_name_match") is True
        if not has_website and not has_name:
            return "missing_identity_signal"
        return None

    if source_kind in {"external_review_site", "google_maps"}:
        if not source_url:
            return "missing_identity_signal"
        return None

    if not source_url:
        return "missing_identity_signal"

    return None


def _is_business_description(text: str) -> bool:
    """Detect business descriptions, staff bios, and service lists masquerading as reviews."""
    lower = text.lower()

    first_person_business = [
        r"\bwe\s+are\b",
        r"\bwe\s+provide\b",
        r"\bwe\s+offer\b",
        r"\bwe\s+specialize\b",
        r"\bour\s+company\b",
        r"\bour\s+team\b",
        r"\bour\s+services\b",
        r"\bour\s+mission\b",
        r"\babout\s+us\b",
    ]
    if any(re.search(p, lower) for p in first_person_business):
        return True

    staff_bio_patterns = [
        r"\b\w+\s+brings?\s+",
        r"\b\w+\s+oversees?\s+",
        r"\b\w+\s+manages?\s+",
        r"\b\w+\s+leads?\s+",
        r"\b\w+\s+handles?\s+",
        r"\b\w+\s+ensures?\s+",
        r"\byour\s+(local\s+)?clients\b",
        r"\bhis\s+business\s+",
        r"\bher\s+business\s+",
    ]
    if any(re.search(p, lower) for p in staff_bio_patterns):
        return True

    company_desc_patterns = [
        r"\b\w+-?owned\s+and\s+operated\b",
        r"\bbased\s+in\s+\w+",
        r"\bwith\s+over\s+\d+\s+years?\s+of\b",
        r"\bfully\s+licensed\b",
        r"\binsured\s+and\s+licensed\b",
        r"\bserving\s+the\s+\w+\s+area\b",
        r"\byour\s+trusted\b",
        r"\bfor\s+over\s+\d+\s+years?\b",
    ]
    if any(re.search(p, lower) for p in company_desc_patterns):
        return True

    service_list_patterns = [
        r"\bcomprehensive\s+range\b",
        r"\bprofessional\s+maintenance\b",
        r"\bquality\s+to\s+ensure\b",
        r"\bfrom\s+\w+\s+to\s+\w+",
        r"\bour\s+crew\b",
        r"\bour\s+experts\b",
    ]
    if any(re.search(p, lower) for p in service_list_patterns):
        return True

    return False


def _candidate_to_review(candidate: dict[str, Any]) -> ReviewEvidence | None:
    review_text = _clean_review_text(candidate.get("review_text"))
    source_url = str(candidate.get("source_url") or "").strip()
    if not review_text or not source_url:
        return None
    signals = {
        key: bool(value)
        for key, value in (candidate.get("identity_match_signals") or {}).items()
        if isinstance(key, str)
    }
    confidence = _coerce_confidence(candidate.get("confidence_score"))
    if confidence is None:
        confidence = score_review_identity_match(signals)
    rating = _coerce_rating(candidate.get("rating"))
    source_name_raw = str(candidate.get("source_name") or "").strip().lower()
    if source_name_raw in {"business_site"}:
        source_kind = "business_site"
    elif source_name_raw in {"external_review_site", "google_maps"}:
        source_kind = "external_review_site"
    else:
        source_kind = "unknown"
    return ReviewEvidence(
        reviewer_name=_clean_optional(candidate.get("reviewer_name")),
        rating=rating,
        review_text=review_text,
        review_date=_coerce_date(candidate.get("review_date")),
        source_url=source_url,
        source_name=_clean_optional(candidate.get("source_name")),
        source_kind=source_kind,
        provenance=_clean_optional(candidate.get("provenance")),
        source_page_type=_clean_optional(candidate.get("page_type")),
        identity_match_signals=signals,
        confidence_score=confidence,
    )


def _clean_review_text(value: Any) -> str | None:
    text = str(value or "").strip()
    if not 25 <= len(text) <= 700:
        return None
    lowered = text.lower()
    if any(token in lowered for token in ["lorem ipsum", "{{", "}}", "as an ai", "todo", "fixme"]):
        return None
    return text


def _clean_optional(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _coerce_rating(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    if rating < 0 or rating > 5:
        return None
    return rating


def _coerce_confidence(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, confidence))


def _coerce_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _combined_signals(reviews: list[ReviewEvidence]) -> dict[str, bool]:
    keys = [
        "business_name_match",
        "phone_match",
        "website_match",
        "location_service_area_match",
        "category_match",
    ]
    return {
        key: any(review.identity_match_signals.get(key) for review in reviews)
        for key in keys
    }


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def _extract_domain(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if not host:
            return None
        host = host.split(":")[0]
        host = host.removeprefix("www.")
        return host or None
    except Exception:
        return None
