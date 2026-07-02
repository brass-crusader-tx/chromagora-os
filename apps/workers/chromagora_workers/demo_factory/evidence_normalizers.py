"""Deterministic evidence normalization for Demo Factory."""

from __future__ import annotations

import html
import re
from typing import Iterable


SERVICE_MARKETING_WORDS = {
    "receive", "ensuring", "guarantee", "replacement", "upgrade", "quote",
    "book", "call", "property", "hydration", "services", "landscaping",
    "lawn care", "yard", "maintenance", "professional", "dedicated",
    "excellence", "quality", "affordable", "best", "top", "expert",
    "reliable", "trusted", "satisfaction", "guaranteed", "free estimate",
    "contact", "visit", "click", "learn more", "read more", "discover",
    "transform", "elevate", "enhance", "revitalize", "restore",
}

SENTENCE_PUNCTUATION = re.compile(r"[.!?;:]")
CONSECUTIVE_SPACES = re.compile(r"\s{2,}")
TRAILING_PUNCTUATION = re.compile(r"[,;:]+$")


def sanitize_location_candidate(value: str) -> str | None:
    """Sanitize a single location candidate. Returns None if invalid."""
    if not value or not isinstance(value, str):
        return None

    cleaned = html.unescape(value).strip()
    cleaned = CONSECUTIVE_SPACES.sub(" ", cleaned)
    cleaned = TRAILING_PUNCTUATION.sub("", cleaned).strip()

    if not cleaned:
        return None
    if len(cleaned) > 60:
        return None
    if len(cleaned) < 2:
        return None

    lowered = cleaned.lower()
    word_count = len(cleaned.split())
    if word_count > 5:
        return None

    if SENTENCE_PUNCTUATION.search(cleaned):
        return None

    for word in SERVICE_MARKETING_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            return None

    if re.match(r"^\d+\s", cleaned):
        return None

    if re.match(r"^[a-z]", cleaned) and not re.match(r"^[a-z]+,", cleaned):
        return None

    return cleaned


def sanitize_service_area_candidates(values: Iterable[str], *, max_items: int = 8) -> list[str]:
    """Sanitize and dedupe location candidates for service_area."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in values:
        cleaned = sanitize_location_candidate(raw)
        if cleaned is None:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= max_items:
            break
    return result
