"""Email service — real sending behind feature flag.

Feature flag: ENABLE_REAL_EMAIL_SENDING (default: false)
When off, email.send_draft is a no-op that logs the attempt.
MessageDraft must be approved before sending.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

ENABLE_REAL_EMAIL = os.environ.get("ENABLE_REAL_EMAIL_SENDING", "false").lower() in ("true", "1", "yes")

# Provider abstraction
PROVIDER = os.environ.get("EMAIL_PROVIDER", "mock")  # mock, sendgrid, ses


def is_real_email_enabled() -> bool:
    """Check if real email sending is enabled."""
    return ENABLE_REAL_EMAIL


def send_email(
    to_address: str,
    subject: str,
    body: str,
    idempotency_key: str,
    from_address: str | None = None,
) -> dict[str, Any]:
    """Send an email. Requires feature flag + approved draft.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Email body text.
        idempotency_key: Unique key to prevent duplicate sends.
        from_address: Sender address (defaults to config).

    Returns:
        Dict with 'sent', 'provider', 'message_id', 'idempotency_key'.
    """
    if not ENABLE_REAL_EMAIL:
        logger.info(
            "Email sending disabled (ENABLE_REAL_EMAIL_SENDING=false). "
            "Would send to=%s subject=%s idem_key=%s",
            to_address, subject, idempotency_key,
        )
        return {
            "sent": False,
            "provider": "mock",
            "message_id": f"mock:{idempotency_key}",
            "idempotency_key": idempotency_key,
            "mock": True,
        }

    if PROVIDER == "sendgrid":
        return _send_via_sendgrid(to_address, subject, body, idempotency_key, from_address)
    elif PROVIDER == "ses":
        return _send_via_ses(to_address, subject, body, idempotency_key, from_address)
    else:
        logger.warning("Unknown EMAIL_PROVIDER=%s, using mock", PROVIDER)
        return {
            "sent": False,
            "provider": "mock",
            "message_id": f"mock:{idempotency_key}",
            "idempotency_key": idempotency_key,
            "mock": True,
        }


def _send_via_sendgrid(
    to_address: str,
    subject: str,
    body: str,
    idempotency_key: str,
    from_address: str | None,
) -> dict[str, Any]:
    """Send via SendGrid API. Requires SENDGRID_API_KEY env var."""
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        logger.error("SENDGRID_API_KEY not configured")
        return {"sent": False, "error": "SendGrid API key not configured"}

    from chromagora_api.services.email_provider import sendgrid_send
    return sendgrid_send(
        api_key=api_key,
        to_address=to_address,
        subject=subject,
        body=body,
        idempotency_key=idempotency_key,
        from_address=from_address or os.environ.get("DEFAULT_FROM_EMAIL", "noreply@chromagora.local"),
    )


def _send_via_ses(
    to_address: str,
    subject: str,
    body: str,
    idempotency_key: str,
    from_address: str | None,
) -> dict[str, Any]:
    """Send via AWS SES. Requires boto3 and AWS credentials."""
    try:
        from chromagora_api.services.email_provider import ses_send
        return ses_send(
            to_address=to_address,
            subject=subject,
            body=body,
            idempotency_key=idempotency_key,
            from_address=from_address or os.environ.get("DEFAULT_FROM_EMAIL", "noreply@chromagora.local"),
        )
    except ImportError:
        logger.error("boto3 not installed, cannot use SES provider")
        return {"sent": False, "error": "boto3 not installed"}
