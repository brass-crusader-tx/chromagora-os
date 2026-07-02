"""Shared helpers for Demo Factory agent boundaries."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def model_artifact_or_fallback(
    model_cls: type[T],
    model_result: dict[str, Any],
    fallback: Callable[[], T],
) -> T:
    """Validate model JSON when available; otherwise return deterministic fallback."""
    if model_result.get("mock"):
        return fallback()
    candidate = model_result.get("content") if isinstance(model_result.get("content"), dict) else model_result
    if not isinstance(candidate, dict) or not candidate:
        return fallback()
    try:
        return model_cls.model_validate(candidate)
    except ValidationError:
        return fallback()
