"""Framework ingestion/retrieval interfaces for Demo Factory.

The repository intentionally contains only retrieval plumbing. Private or
licensed framework corpus material should be inserted into Supabase outside
source control.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml


DEFAULT_FRAMEWORK_TAGS = [
    "value_equation",
    "grand_slam_offer",
    "risk_reversal",
    "dream_outcome",
    "perceived_likelihood",
    "time_delay",
    "effort_sacrifice",
    "proof_stack",
    "offer_stack",
    "CTA_hierarchy",
    "objection_collapse",
    "problem_agitation",
]


def upsert_framework_source(
    *,
    sb,
    tenant_id: UUID,
    source_key: str,
    title: str,
    source_type: str = "private_corpus",
    license_scope: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "tenant_id": str(tenant_id),
        "source_key": source_key,
        "title": title,
        "source_type": source_type,
        "license_scope": license_scope,
        "metadata_json": metadata_json or {},
    }
    resp = sb.table("demo_site_framework_sources").upsert(
        payload,
        on_conflict="tenant_id,source_key",
    ).execute()
    return (resp.data or [payload])[0]


def add_framework_pattern(
    *,
    sb,
    tenant_id: UUID,
    source_id: UUID | str | None,
    pattern_key: str,
    title: str,
    tags: list[str],
    pattern_json: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "source_id": str(source_id) if source_id else None,
        "pattern_key": pattern_key,
        "title": title,
        "tags": tags,
        "pattern_json": pattern_json,
    }
    resp = sb.table("demo_site_framework_patterns").insert(payload).execute()
    return (resp.data or [payload])[0]


def retrieve_framework_patterns(
    *,
    sb,
    tenant_id: UUID,
    project_id: UUID,
    tags: list[str] | None = None,
    limit: int = 8,
    query_json: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    selected_tags = tags or DEFAULT_FRAMEWORK_TAGS[:6]
    query = (
        sb.table("demo_site_framework_patterns")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .limit(limit)
    )
    # Supabase/PostgREST array overlap filters vary by client version. Load a
    # small tenant-scoped window and filter in Python for the v0.1 interface.
    resp = query.execute()
    patterns = resp.data or []
    filtered = [
        pattern
        for pattern in patterns
        if not selected_tags or set(pattern.get("tags") or []).intersection(selected_tags)
    ][:limit]
    if not filtered:
        filtered = _load_local_strategy_patterns(selected_tags, limit)

    retrieval_payload = {
        "tenant_id": str(tenant_id),
        "project_id": str(project_id),
        "stage": "conversion_strategy",
        "query_json": query_json or {"tags": selected_tags, "limit": limit},
        "selected_pattern_ids": [row["id"] for row in filtered if row.get("id")],
        "result_json": {"patterns": filtered},
    }
    try:
        sb.table("demo_site_framework_retrievals").insert(retrieval_payload).execute()
    except Exception:
        pass
    return filtered


def _load_local_strategy_patterns(selected_tags: list[str], limit: int) -> list[dict[str, Any]]:
    pack_dir = Path(
        os.getenv("DEMO_FACTORY_STRATEGY_PACK_DIR")
        or Path(__file__).resolve().parents[1] / "strategy_knowledge"
    )
    patterns: list[dict[str, Any]] = []
    for pack_path in [
        pack_dir / "offer_strategy_pack.yaml",
        pack_dir / "lead_strategy_pack.yaml",
        pack_dir / "money_model_pack.yaml",
        pack_dir / "avatar_pack.yaml",
    ]:
        if not pack_path.exists():
            continue
        try:
            pack = yaml.safe_load(pack_path.read_text()) or {}
        except Exception:
            continue
        for pattern in pack.get("patterns", []):
            tags = pattern.get("tags") or []
            if selected_tags and not set(tags).intersection(selected_tags):
                continue
            patterns.append(
                {
                    "source_key": pack.get("source_key"),
                    "pattern_key": pattern.get("pattern_key"),
                    "title": pattern.get("title"),
                    "tags": tags,
                    "pattern_json": pattern.get("pattern_json") or {},
                    "metadata_json": {"local_distilled_pack": str(pack_path)},
                }
            )
            if len(patterns) >= limit:
                return patterns
    return patterns[:limit]
