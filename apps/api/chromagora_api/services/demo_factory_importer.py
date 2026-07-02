"""CSV import service for Demo Factory lead batches."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4


RECOGNIZED_COLUMNS = {
    "Rank",
    "Business Name",
    "Website URL",
    "Website Domain",
    "Demo URL / Slug",
    "Build Status",
    "Verify Before Build",
    "Visible Site Gap Summary",
    "Website Weakness / Redesign Delta",
    "Before/After Slider Angle",
    "Suggested Demo CTA",
    "Demo Angle",
    "Backend Hook",
    "Scoring Notes",
}


@dataclass
class NormalizedLeadRow:
    original_row_number: int
    row_number: int
    rank: float | None
    business_name: str
    website_url: str | None
    website_domain: str | None
    demo_slug: str
    verify_before_build: bool
    raw_row_json: dict[str, Any]


def parse_rank(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value: Any, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "verify", "before build"}:
        return True
    if text in {"0", "false", "no", "n", "skip", "unchecked"}:
        return False
    return default


def slugify(value: str, fallback: str = "demo") -> str:
    text = value.strip().lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or fallback


def normalize_domain(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "://" not in text:
        text_for_parse = f"https://{text}"
    else:
        text_for_parse = text
    parsed = urlparse(text_for_parse)
    host = (parsed.netloc or parsed.path.split("/", 1)[0]).lower().strip()
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalize_website_url(url_value: str | None, domain_value: str | None = None) -> tuple[str | None, str | None]:
    source = (url_value or "").strip() or (domain_value or "").strip()
    if not source:
        return None, normalize_domain(domain_value)
    if "://" not in source:
        source = f"https://{source}"
    parsed = urlparse(source)
    domain = normalize_domain(parsed.netloc or parsed.path)
    if not domain:
        return None, normalize_domain(domain_value)
    path = parsed.path if parsed.netloc else ""
    normalized_url = f"{parsed.scheme or 'https'}://{domain}{path or ''}"
    return normalized_url.rstrip("/"), domain


def slug_from_demo_field(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = parsed.netloc.lower()
    if host.endswith(".demo.chromagora.com"):
        return slugify(host.removesuffix(".demo.chromagora.com"))
    path = parsed.path.strip("/")
    if path:
        return slugify(path.split("/")[-1])
    return slugify(text)


def _is_blank_row(row: dict[str, Any]) -> bool:
    return not any(str(value).strip() for value in row.values() if value is not None)


def _decode_csv(csv_bytes: bytes) -> list[dict[str, Any]]:
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(reader, start=1):
        normalized = {str(k).strip() if k is not None else "": v for k, v in row.items()}
        if _is_blank_row(normalized):
            continue
        normalized["_csv_row_number"] = index
        rows.append(normalized)
    return rows


def normalize_csv_rows(csv_bytes: bytes) -> list[NormalizedLeadRow]:
    raw_rows = _decode_csv(csv_bytes)
    normalized: list[NormalizedLeadRow] = []
    used_slugs: set[str] = set()

    def sort_key(row: dict[str, Any]) -> tuple[int, float | int]:
        rank = parse_rank(row.get("Rank"))
        if rank is not None:
            return (0, rank)
        return (1, int(row.get("_csv_row_number") or 0))

    for processing_number, row in enumerate(sorted(raw_rows, key=sort_key), start=1):
        rank = parse_rank(row.get("Rank"))
        business_name = str(row.get("Business Name") or "").strip()
        website_url, website_domain = normalize_website_url(row.get("Website URL"), row.get("Website Domain"))
        if not business_name:
            business_name = website_domain or f"CSV Row {row.get('_csv_row_number')}"

        base_slug = (
            slug_from_demo_field(row.get("Demo URL / Slug"))
            or slugify(business_name)
            or slugify(website_domain or "", fallback=f"demo-{processing_number}")
        )
        demo_slug = base_slug
        suffix = 2
        while demo_slug in used_slugs:
            demo_slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(demo_slug)

        raw_row_json = dict(row)
        raw_row_json["_recognized_columns"] = {
            column: row.get(column)
            for column in RECOGNIZED_COLUMNS
            if column in row
        }

        normalized.append(
            NormalizedLeadRow(
                original_row_number=int(row.get("_csv_row_number") or processing_number),
                row_number=processing_number,
                rank=rank,
                business_name=business_name,
                website_url=website_url,
                website_domain=website_domain,
                demo_slug=demo_slug,
                verify_before_build=parse_bool(row.get("Verify Before Build"), default=True),
                raw_row_json=raw_row_json,
            )
        )

    return normalized


def infer_name_from_domain(domain: str | None) -> str | None:
    """Create a human-ish business label from a public domain."""
    if not domain:
        return None
    root = domain.lower().removeprefix("www.").split(".")[0]
    words = [word for word in re.split(r"[-_]+", root) if word]
    if not words:
        return None
    return " ".join(word.capitalize() for word in words)


def _emit_event(sb, tenant_id: UUID, event_type: str, payload: dict[str, Any], trace_id: str | None = None) -> None:
    try:
        sb.table("events").insert(
            {
                "tenant_id": str(tenant_id),
                "event_type": event_type,
                "source_type": "demo_factory",
                "payload_json": payload,
                "trace_id": trace_id,
                "entity_type": payload.get("entity_type"),
                "entity_id": payload.get("entity_id"),
                "idempotency_key": payload.get("idempotency_key"),
            }
        ).execute()
    except Exception:
        # Import should not fail just because observability tables are not ready.
        pass


def import_demo_csv(
    *,
    csv_bytes: bytes,
    source_filename: str,
    tenant_id: UUID,
    sb,
) -> dict[str, Any]:
    """Create a Demo Factory batch, rows, and projects from a CSV body."""
    rows = normalize_csv_rows(csv_bytes)
    return create_demo_batch_from_normalized_rows(
        rows=rows,
        source_filename=source_filename,
        tenant_id=tenant_id,
        sb=sb,
        batch_metadata={"importer": "demo_factory_importer", "intake_type": "csv"},
    )


def create_demo_batch_from_normalized_rows(
    *,
    rows: list[NormalizedLeadRow],
    source_filename: str,
    tenant_id: UUID,
    sb,
    batch_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a Demo Factory batch, rows, and projects from normalized input rows."""
    if not rows:
        raise ValueError("Demo import did not contain any usable rows")

    batch_id = uuid4()
    metadata_json = {"importer": "demo_factory_importer", **(batch_metadata or {})}
    batch_payload = {
        "id": str(batch_id),
        "tenant_id": str(tenant_id),
        "source_filename": source_filename or "demo-factory-import.csv",
        "total_rows": len(rows),
        "queued_count": len(rows),
        "running_count": 0,
        "published_count": 0,
        "failed_count": 0,
        "current_row_number": rows[0].row_number if rows else None,
        "status": "queued",
        "metadata_json": metadata_json,
    }
    sb.table("demo_site_batches").insert(batch_payload).execute()

    created_rows: list[dict[str, Any]] = []
    existing_slugs = _existing_demo_slugs(sb, tenant_id)
    used_slugs: set[str] = set()
    for row in rows:
        row.demo_slug = _dedupe_slug(row.demo_slug, existing_slugs | used_slugs)
        used_slugs.add(row.demo_slug)
        row_id = uuid4()
        project_id = uuid4()
        trace_id = f"demo-site:{batch_id}:{row.row_number}"
        demo_host = f"{row.demo_slug}.demo.chromagora.com"

        row_payload = {
            "id": str(row_id),
            "tenant_id": str(tenant_id),
            "batch_id": str(batch_id),
            "project_id": None,
            "row_number": row.row_number,
            "rank": row.rank,
            "business_name": row.business_name,
            "website_url": row.website_url,
            "website_domain": row.website_domain,
            "demo_slug": row.demo_slug,
            "raw_row_json": row.raw_row_json,
            "status": "queued",
        }
        sb.table("demo_site_batch_rows").insert(row_payload).execute()

        project_payload = {
            "id": str(project_id),
            "tenant_id": str(tenant_id),
            "business_id": None,
            "batch_id": str(batch_id),
            "batch_row_id": str(row_id),
            "source_domain": row.website_domain,
            "normalized_domain": row.website_domain,
            "source_url": row.website_url,
            "business_name": row.business_name,
            "demo_slug": row.demo_slug,
            "demo_host": demo_host,
            "status": "queued",
            "current_stage": "queued",
            "verify_before_build": row.verify_before_build,
            "priority_score": row.rank,
            "input_row_json": row.raw_row_json,
            "trace_id": trace_id,
        }
        sb.table("demo_site_projects").insert(project_payload).execute()
        sb.table("demo_site_batch_rows").update({"project_id": str(project_id)}).eq("id", str(row_id)).execute()

        _emit_event(
            sb,
            tenant_id,
            "demo_site.project_queued",
            {
                "entity_type": "demo_site_project",
                "entity_id": str(project_id),
                "batch_id": str(batch_id),
                "batch_row_id": str(row_id),
                "row_number": row.row_number,
                "business_name": row.business_name,
                "idempotency_key": f"demo_site.project_queued:{project_id}",
            },
            trace_id=trace_id,
        )

        created = {**row_payload, "project_id": str(project_id), "project": project_payload}
        created_rows.append(created)

    _emit_event(
        sb,
        tenant_id,
        "demo_site.batch_imported",
        {
            "entity_type": "demo_site_batch",
            "entity_id": str(batch_id),
            "batch_id": str(batch_id),
            "source_filename": source_filename,
            "total_rows": len(rows),
            "idempotency_key": f"demo_site.batch_imported:{batch_id}",
        },
    )

    return {
        "batch": batch_payload,
        "rows": created_rows,
        "projects_created": len(created_rows),
    }


def _existing_demo_slugs(sb, tenant_id: UUID) -> set[str]:
    try:
        resp = (
            sb.table("demo_site_projects")
            .select("demo_slug")
            .eq("tenant_id", str(tenant_id))
            .execute()
        )
        return {str(row.get("demo_slug")) for row in (resp.data or []) if row.get("demo_slug")}
    except Exception:
        return set()


def _dedupe_slug(base_slug: str, unavailable: set[str]) -> str:
    base = slugify(base_slug)
    candidate = base
    suffix = 2
    while candidate in unavailable:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate
