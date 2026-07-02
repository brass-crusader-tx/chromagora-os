"""Link-drop intake for Demo Factory.

This path intentionally creates a one-row batch so CSV and link-drop projects
flow through the same worker, row state, cockpit, and renderer machinery.
"""

from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID

from pydantic import BaseModel, Field

from chromagora_api.services.demo_factory_importer import (
    NormalizedLeadRow,
    create_demo_batch_from_normalized_rows,
    infer_name_from_domain,
    parse_bool,
    slugify,
)


TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "gbraid",
    "wbraid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "msclkid",
}
BLOCKED_SCHEMES = {"mailto", "tel", "file", "javascript", "data"}


class DemoLinkDropInput(BaseModel):
    website_url: str = Field(min_length=1)
    business_name: str | None = None
    suggested_demo_cta: str | None = None
    demo_angle: str | None = None
    before_after_slider_angle: str | None = None
    backend_hook: str | None = None
    verify_before_build: bool = True
    auto_start: bool = True


def import_demo_link_drop(
    *,
    payload: DemoLinkDropInput,
    tenant_id: UUID,
    sb,
) -> dict[str, Any]:
    """Create a one-row Demo Factory batch from a pasted website link."""
    normalized_url, domain = validate_public_website_url(payload.website_url)
    business_name = (payload.business_name or "").strip() or infer_name_from_domain(domain) or domain
    domain_root = domain.split(".", 1)[0]
    base_slug = slugify(business_name or domain_root, fallback=slugify(domain_root, fallback="demo"))

    raw_row_json = {
        "Rank": "1",
        "Business Name": business_name,
        "Website URL": normalized_url,
        "Website Domain": domain,
        "Suggested Demo CTA": payload.suggested_demo_cta or "",
        "Demo Angle": payload.demo_angle or "",
        "Before/After Slider Angle": payload.before_after_slider_angle or "",
        "Backend Hook": payload.backend_hook or "",
        "Verify Before Build": str(payload.verify_before_build),
        "_intake_type": "link_drop",
        "_original_website_url": payload.website_url,
        "_operator_notes": _operator_notes(payload),
    }
    row = NormalizedLeadRow(
        original_row_number=1,
        row_number=1,
        rank=1,
        business_name=business_name,
        website_url=normalized_url,
        website_domain=domain,
        demo_slug=base_slug,
        verify_before_build=parse_bool(payload.verify_before_build, default=True),
        raw_row_json=raw_row_json,
    )
    result = create_demo_batch_from_normalized_rows(
        rows=[row],
        source_filename=f"link-drop-{domain}.csv",
        tenant_id=tenant_id,
        sb=sb,
        batch_metadata={
            "intake_type": "link_drop",
            "source_url": normalized_url,
            "original_input": payload.website_url,
            "operator_notes": _operator_notes(payload),
            "auto_start": payload.auto_start,
        },
    )
    project = result["rows"][0]["project"] if result.get("rows") else None
    return {
        **result,
        "project": project,
        "project_url": f"/demo-factory/projects/{project['id']}" if project else None,
    }


def validate_public_website_url(value: str) -> tuple[str, str]:
    """Return a canonical public http(s) URL and normalized domain."""
    text = (value or "").strip()
    if not text:
        raise ValueError("Website URL is required")

    first_parse = urlparse(text)
    if first_parse.scheme.lower() in BLOCKED_SCHEMES:
        raise ValueError(f"Unsupported URL scheme: {first_parse.scheme}")
    if not first_parse.scheme:
        text = f"https://{text}"

    parsed = urlparse(text)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("Website URL must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("Website URL must not include credentials")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise ValueError("Website URL must include a public hostname")
    _reject_private_host(host)

    domain = host[4:] if host.startswith("www.") else host
    query = _strip_tracking_query(parsed.query)
    path = "" if parsed.path == "/" else parsed.path or ""
    canonical = urlunparse(
        (
            scheme,
            domain,
            path,
            "",
            query,
            "",
        )
    ).rstrip("/")
    return canonical, domain


def _strip_tracking_query(query: str) -> str:
    kept = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in TRACKING_QUERY_KEYS or any(lowered.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        kept.append((key, value))
    return urlencode(kept, doseq=True)


def _reject_private_host(host: str) -> None:
    if host in {"localhost", "0.0.0.0"} or host.endswith(".localhost"):
        raise ValueError("Website URL must be a public website, not localhost")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        raise ValueError("Website URL must not point to a private or local IP address")


def _operator_notes(payload: DemoLinkDropInput) -> dict[str, Any]:
    return {
        "suggested_demo_cta": payload.suggested_demo_cta,
        "demo_angle": payload.demo_angle,
        "before_after_slider_angle": payload.before_after_slider_angle,
        "backend_hook": payload.backend_hook,
    }
