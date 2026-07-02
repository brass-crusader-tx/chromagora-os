"""Centralized demo slug/host helpers for Demo Factory."""

from __future__ import annotations

import re
from urllib.parse import urlparse

CANONICAL_DEMO_SUFFIX = ".demo.chromagora.com"


def canonical_demo_slug(input_str: str) -> str:
    """Convert a business name or slug to canonical hyphen-preserving form."""
    slug = input_str.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug or "demo"


def canonical_demo_host(slug: str) -> str:
    """Build canonical demo host from slug."""
    return f"{slug}{CANONICAL_DEMO_SUFFIX}"


def canonical_demo_url(slug: str) -> str:
    """Build canonical demo URL from slug."""
    return f"https://{canonical_demo_host(slug)}"


def slug_from_demo_host(host: str) -> str | None:
    """Extract slug from a demo host. Returns None if not a demo host."""
    host = host.lower().split(":")[0]
    host = host.removeprefix("www.")
    if not host.endswith(CANONICAL_DEMO_SUFFIX):
        return None
    slug = host[: -len(CANONICAL_DEMO_SUFFIX)]
    return slug or None


def is_demo_host(host: str) -> bool:
    """Check if a host is a demo host."""
    return slug_from_demo_host(host) is not None
