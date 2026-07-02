"""Adversarial owner-reaction checker."""

from __future__ import annotations

import json
from uuid import UUID

from chromagora_schemas.demo_factory import AdversarialOwnerReactionReport, SiteSpec

from chromagora_workers.demo_factory.model_gateway import call_agent_model
from chromagora_workers.demo_factory.agents.utils import model_artifact_or_fallback


BLOCKED_TEXT_MARKERS = ["lorem ipsum", "as an ai", "ai-generated", "todo", "fixme", "{{"]


def run_adversarial_checker_agent(*, project_id: UUID, site_spec: SiteSpec) -> AdversarialOwnerReactionReport:
    model_result = call_agent_model(
        "adversarial_checker",
        project_id,
        "adversarial_checker",
        "Find fake, embarrassing, irrelevant, generic, or AI-looking material.",
        site_spec.model_dump(mode="json"),
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
    report.passed = report.passed and not report.blocking_issues
    if report.blocking_issues:
        report.owner_reaction_risk_score = max(report.owner_reaction_risk_score, 0.85)
    return report
