"""Build compact evidence bundles for Demo Factory agents."""

from __future__ import annotations

from typing import Any

from chromagora_workers.demo_factory.evidence_normalizers import sanitize_service_area_candidates


def build_evidence_bundle(
    project: dict[str, Any],
    snapshots: list[dict[str, Any]] | None = None,
    assets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    raw_row = project.get("input_row_json") or {}
    snapshots = _dedupe_snapshots(snapshots or [])
    assets = _dedupe_assets(assets or [])
    metadata_rows = [row.get("metadata_json") or {} for row in snapshots]

    contact_candidates = _merge_contact_candidates(metadata_rows)
    service_candidates = _merge_unique(
        _flatten(meta.get("service_candidates") for meta in metadata_rows)
        + _service_candidates_from_row(raw_row)
    )
    location_candidates = sanitize_service_area_candidates(
        _merge_unique(_flatten(meta.get("location_candidates") for meta in metadata_rows)),
        max_items=8,
    )
    image_candidates = _merge_unique(
        _flatten(meta.get("image_candidates") for meta in metadata_rows)
        + [asset.get("source_url") for asset in assets if asset.get("asset_type") == "image_candidate"]
    )
    logo_candidates = _merge_unique(_flatten(meta.get("logo_candidates") for meta in metadata_rows))
    review_source_candidates = _merge_review_source_candidates(snapshots)
    color_candidates = _merge_unique(_flatten(meta.get("color_candidates") for meta in metadata_rows)) or [
        "#1f2937",
        "#2563eb",
        "#f8fafc",
    ]
    old_screenshot = next((asset for asset in assets if asset.get("asset_type") == "old_site_screenshot"), None)

    return {
        "business_name": project.get("business_name"),
        "source_url": project.get("source_url"),
        "source_domain": project.get("normalized_domain") or project.get("source_domain"),
        "crawl_text_summaries": [
            _trim_text(row.get("text_summary"), 700) for row in snapshots if row.get("text_summary")
        ][:8],
        "crawl_pages": [
            {
                "page_type": row.get("page_type"),
                "source_url": row.get("source_url"),
                "final_url": row.get("final_url"),
                "title": row.get("title"),
                "summary": _trim_text(row.get("text_summary"), 700),
            }
            for row in snapshots
        ][:8],
        "contact_candidates": contact_candidates,
        "service_candidates": service_candidates[:10],
        "location_service_area_candidates": location_candidates[:10],
        "image_asset_candidates": image_candidates[:30],
        "logo_candidates": logo_candidates[:10],
        "review_source_candidates": review_source_candidates[:10],
        "colors_logo_candidates": color_candidates[:8],
        "old_site_screenshot_url": old_screenshot.get("public_url") if old_screenshot else None,
        "old_site_weakness_notes": raw_row.get("Website Weakness / Redesign Delta")
        or raw_row.get("Visible Site Gap Summary"),
        "before_after_slider_angle": raw_row.get("Before/After Slider Angle"),
        "suggested_demo_cta": raw_row.get("Suggested Demo CTA") or "Request a quote",
        "demo_angle": raw_row.get("Demo Angle"),
        "backend_hook": raw_row.get("Backend Hook"),
        "scoring_notes": raw_row.get("Scoring Notes"),
    }


def _merge_contact_candidates(metadata_rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    phones: list[str] = []
    emails: list[str] = []
    for meta in metadata_rows:
        contacts = meta.get("contact_candidates") or {}
        phones.extend(contacts.get("phones") or [])
        emails.extend(contacts.get("emails") or [])
    return {"phones": _merge_unique(phones)[:5], "emails": _merge_unique(emails)[:5]}


def _service_candidates_from_row(raw_row: dict[str, Any]) -> list[str]:
    notes = " ".join(
        str(raw_row.get(key) or "")
        for key in [
            "Visible Site Gap Summary",
            "Website Weakness / Redesign Delta",
            "Demo Angle",
            "Scoring Notes",
        ]
    ).lower()
    candidates: list[str] = []
    for label in [
        "landscaping",
        "lawn care",
        "snow removal",
        "roofing",
        "cleaning",
        "remodeling",
        "plumbing",
        "hvac",
        "painting",
    ]:
        if label in notes:
            candidates.append(label.title())
    return candidates


def _flatten(values) -> list[str]:
    flattened: list[str] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(str(item) for item in value if item)
        elif value:
            flattened.append(str(value))
    return flattened


def _merge_unique(values: list[Any]) -> list[str]:
    merged: list[str] = []
    for value in values:
        if not value:
            continue
        text = str(value).strip()
        if text and text not in merged:
            merged.append(text)
    return merged


def _dedupe_snapshots(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(snapshots, key=lambda row: str(row.get("created_at") or ""), reverse=True)
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for snapshot in ordered:
        key = (
            str(snapshot.get("page_type") or ""),
            str(snapshot.get("final_url") or snapshot.get("source_url") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        trimmed = dict(snapshot)
        if trimmed.get("visible_text"):
            trimmed["visible_text"] = _trim_text(trimmed.get("visible_text"), 2400)
        if trimmed.get("text_summary"):
            trimmed["text_summary"] = _trim_text(trimmed.get("text_summary"), 900)
        merged.append(trimmed)
        if len(merged) >= 8:
            break
    return list(reversed(merged))


def _dedupe_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(assets, key=lambda row: str(row.get("created_at") or ""), reverse=True)
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for asset in ordered:
        key = (
            str(asset.get("asset_type") or ""),
            str(asset.get("source_url") or asset.get("public_url") or asset.get("storage_path") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        selected.append(asset)
        if len(selected) >= 60:
            break
    return selected


def _trim_text(value: Any, limit: int) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def _merge_review_source_candidates(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for snapshot in snapshots:
        metadata = snapshot.get("metadata_json") or {}
        for candidate in metadata.get("testimonial_candidates") or []:
            if not isinstance(candidate, dict):
                continue
            review_text = str(candidate.get("review_text") or "").strip()
            source_url = str(candidate.get("source_url") or snapshot.get("final_url") or snapshot.get("source_url") or "")
            if not review_text or not source_url:
                continue
            key = (source_url, review_text[:160])
            if key in seen:
                continue
            seen.add(key)
            enriched = dict(candidate)
            enriched.setdefault("source_name", "business_site")
            enriched["source_url"] = source_url
            enriched.setdefault("page_type", snapshot.get("page_type"))
            merged.append(enriched)
    return merged
