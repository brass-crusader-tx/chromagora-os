"""Adversarial owner-reaction checker."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from chromagora_schemas.demo_factory import AdversarialOwnerReactionReport, SiteSpec

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback


BLOCKED_TEXT_MARKERS = ["lorem ipsum", "as an ai", "ai-generated", "todo", "fixme", "{{"]

REVIEW_POLICY = """
Review Evidence Policy:
- Business-site testimonials are acceptable when:
  - source_kind == "business_site"
  - source_url domain matches the crawled official website
  - identity_signals.website is true or identity_signals.business_name is true
  - quote text was scraped, not generated
- Label them internally as "self-published testimonials", not "independent reviews".
- Third-party reviews are acceptable when source_kind is "external_review_site" or "google_maps".
- Invented or unproven reviews must always block.
- Do NOT block valid self-published testimonials when deterministic provenance confirms them.
"""


def run_adversarial_checker_agent(
    *,
    project_id: UUID,
    site_spec: SiteSpec,
    evidence_bundle: dict[str, Any] | None = None,
    deterministic_qa_result: Any | None = None,
) -> AdversarialOwnerReactionReport:
    context = site_spec.model_dump(mode="json")
    if evidence_bundle:
        context["_evidence_summary"] = {
            "source_domain": evidence_bundle.get("source_domain"),
            "source_url": evidence_bundle.get("source_url"),
        }
    if deterministic_qa_result:
        context["_deterministic_qa"] = {
            "passed": deterministic_qa_result.passed,
            "failures": [f.model_dump(mode="json") for f in deterministic_qa_result.failures],
        }

    review_provenance_summary = []
    for review in site_spec.reviews:
        review_provenance_summary.append({
            "source_kind": getattr(review, "source_kind", "unknown"),
            "source_url": review.source_url,
            "confidence_score": review.confidence_score,
            "identity_match_signals": review.identity_match_signals,
        })

    system_prompt = (
        "Find fake, embarrassing, irrelevant, generic, or AI-looking material. "
        + REVIEW_POLICY
        + "\nReview Provenance Summary:\n"
        + json.dumps(review_provenance_summary, sort_keys=True, default=str)
        + "\nDeterministic QA Result: "
        + ("PASSED" if not deterministic_qa_result or deterministic_qa_result.passed else "FAILED")
    )

    model_result = call_agent_model(
        "adversarial_checker",
        project_id,
        "adversarial_checker",
        system_prompt,
        context,
        AdversarialOwnerReactionReport.model_json_schema(),
        temperature=0,
        max_tokens=4096,
        timeout_seconds=420,
    )
    serialized = json.dumps(site_spec.model_dump(mode="json"), sort_keys=True).lower()
    blocking = [marker for marker in BLOCKED_TEXT_MARKERS if marker in serialized]

    def fallback() -> AdversarialOwnerReactionReport:
        return AdversarialOwnerReactionReport(
            project_id=project_id,
            passed=not blocking,
            blocking_issues=[f"Blocked marker found: {marker}" for marker in blocking],
            warnings=[],
            suggested_fixes=[],
            owner_reaction_risk_score=0.85 if blocking else 0.1,
        )

    report = model_artifact_or_fallback(AdversarialOwnerReactionReport, model_result, fallback)
    marker_issues = [f"Blocked marker found: {marker}" for marker in blocking]
    report.blocking_issues = list(dict.fromkeys(report.blocking_issues + marker_issues))

    report.blocking_issues = _downgrade_self_published_testimonial_blocks(
        report.blocking_issues, site_spec, evidence_bundle
    )

    report.passed = report.passed and not report.blocking_issues
    if report.blocking_issues:
        report.owner_reaction_risk_score = max(report.owner_reaction_risk_score, 0.85)
    return report


def _downgrade_self_published_testimonial_blocks(
    blocking_issues: list[str],
    site_spec: SiteSpec,
    evidence_bundle: dict[str, Any] | None,
) -> list[str]:
    """Remove blocking issues that are valid self-published testimonials."""
    if not blocking_issues:
        return blocking_issues

    source_domain = ""
    if evidence_bundle:
        source_domain = (evidence_bundle.get("source_domain") or "").lower().strip()

    valid_self_published = set()
    for review in site_spec.reviews:
        if getattr(review, "source_kind", None) != "business_site":
            continue
        signals = review.identity_match_signals or {}
        has_website = signals.get("website_match") is True
        has_name = signals.get("business_name_match") is True
        if has_website or has_name:
            valid_self_published.add(review.review_text.strip().lower()[:100])

    filtered = []
    for issue in blocking_issues:
        issue_lower = issue.lower()
        is_testimonial_block = any(
            term in issue_lower
            for term in ["testimonial", "review", "self-published", "fake review", "invented"]
        )
        if is_testimonial_block and valid_self_published:
            matched = any(
                snippet in issue_lower
                for snippet in valid_self_published
            )
            if matched:
                continue
        filtered.append(issue)
    return filtered
