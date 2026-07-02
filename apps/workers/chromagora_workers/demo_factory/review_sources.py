"""Grounded review/testimonial sourcing for Demo Factory."""

from __future__ import annotations

from datetime import date
from typing import Any

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
    return ReviewEvidence(
        reviewer_name=_clean_optional(candidate.get("reviewer_name")),
        rating=rating,
        review_text=review_text,
        review_date=_coerce_date(candidate.get("review_date")),
        source_url=source_url,
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
