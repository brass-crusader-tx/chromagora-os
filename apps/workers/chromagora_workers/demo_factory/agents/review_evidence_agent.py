"""Review evidence agent boundary."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from chromagora_schemas.demo_factory import ReviewEvidenceBlock, score_review_identity_match

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback
from chromagora_workers.demo_factory.review_sources import build_grounded_review_evidence


def run_review_evidence_agent(*, project_id: UUID, evidence_bundle: dict[str, Any]) -> ReviewEvidenceBlock:
    grounded_evidence = build_grounded_review_evidence(evidence_bundle)
    context_packet = dict(evidence_bundle)
    context_packet["grounded_review_evidence"] = grounded_evidence.model_dump(mode="json")
    model_result = call_agent_model(
        "review_evidence",
        project_id,
        "review_evidence",
        (
            "Verify exact-business reviews. Select only reviews present in grounded_review_evidence. "
            "Do not invent, paraphrase into a new review, or use reviews when confidence is low."
        ),
        context_packet,
        ReviewEvidenceBlock.model_json_schema(),
        temperature=0,
        max_tokens=4096,
        timeout_seconds=600,
    )

    def fallback() -> ReviewEvidenceBlock:
        signals = {
            "business_name_match": False,
            "phone_match": False,
            "website_match": False,
            "location_service_area_match": False,
            "category_match": False,
        }
        return ReviewEvidenceBlock(
            selected_reviews=[],
            rejected_reviews=[],
            source_urls=[],
            identity_match_signals=signals,
            confidence_score=score_review_identity_match(signals),
            omit_review_section=True,
        )

    block = model_artifact_or_fallback(ReviewEvidenceBlock, model_result, fallback)
    if grounded_evidence.selected_reviews:
        block.selected_reviews = [
            review for review in block.selected_reviews if _review_is_grounded(review, grounded_evidence)
        ]
        if not block.selected_reviews:
            block = grounded_evidence
    else:
        block.selected_reviews = []
    if block.confidence_score < 0.65 or not block.selected_reviews:
        block.omit_review_section = True
        block.selected_reviews = []
    block.selected_reviews = block.selected_reviews[:5]
    return block


def _review_is_grounded(review, grounded_evidence: ReviewEvidenceBlock) -> bool:
    review_text = (review.review_text or "").strip().lower()
    source_url = (review.source_url or "").strip()
    if not review_text or not source_url:
        return False
    for grounded in grounded_evidence.selected_reviews:
        grounded_text = grounded.review_text.strip().lower()
        if review_text == grounded_text and source_url == grounded.source_url:
            return True
        if review_text in grounded_text or grounded_text in review_text:
            return source_url == grounded.source_url
    return False
