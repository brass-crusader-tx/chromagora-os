"""Typed exceptions for Demo Factory runtime failure classification."""

from __future__ import annotations


class DemoFactoryError(Exception):
    """Base Demo Factory error."""


class DemoFactoryTransientError(DemoFactoryError):
    """Retryable provider/network failure."""


class DemoFactoryConfigError(DemoFactoryError):
    """Terminal configuration error (missing API key, missing zone)."""


class DemoFactoryProviderBillingError(DemoFactoryError):
    """Provider billing error (402 insufficient credits)."""


class DemoFactoryQAError(DemoFactoryError):
    """QA failure that blocks publish."""


class DemoFactoryCodeBugError(DemoFactoryError):
    """Unexpected code error (should be filed as a bug)."""


class DemoFactoryRateLimitError(DemoFactoryError):
    """Rate limit error (should wait before retrying)."""


def classify_failure(exc: Exception) -> tuple[str, str]:
    """Classify an exception into (status_code, error_class)."""
    if isinstance(exc, DemoFactoryProviderBillingError):
        return "failed_terminal", "provider_billing_blocked"
    if isinstance(exc, DemoFactoryConfigError):
        return "failed_terminal", "config_blocked"
    if isinstance(exc, DemoFactoryCodeBugError):
        return "failed_terminal", "code_bug"
    if isinstance(exc, DemoFactoryRateLimitError):
        return "waiting_rate_limit", "rate_limited"
    if isinstance(exc, DemoFactoryQAError):
        return "failed_retryable", "qa_blocked"
    if isinstance(exc, DemoFactoryTransientError):
        return "failed_retryable", "transient"
    if isinstance(exc, DemoFactoryError):
        return "failed_retryable", "unknown_error"
    return "failed_retryable", "unclassified"
