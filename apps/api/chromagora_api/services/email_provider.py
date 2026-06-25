"""Email provider implementations.

Abstracted behind email_service for pluggable providers.
Only loaded when ENABLE_REAL_EMAIL_SENDING=true.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def sendgrid_send(
    api_key: str,
    to_address: str,
    subject: str,
    body: str,
    idempotency_key: str,
    from_address: str,
) -> dict[str, Any]:
    """Send email via SendGrid v3 API."""
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "personalizations": [{"to": [{"email": to_address}]}],
        "from": {"email": from_address},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
        "custom_args": {"idempotency_key": idempotency_key},
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            message_id = resp.headers.get("X-Message-Id", f"sg:{idempotency_key}")
            logger.info("Email sent via SendGrid: %s -> %s", idempotency_key, to_address)
            return {
                "sent": True,
                "provider": "sendgrid",
                "message_id": message_id,
                "idempotency_key": idempotency_key,
            }
    except Exception as exc:
        logger.error("SendGrid send failed: %s", exc)
        return {
            "sent": False,
            "provider": "sendgrid",
            "error": str(exc),
            "idempotency_key": idempotency_key,
        }


def ses_send(
    to_address: str,
    subject: str,
    body: str,
    idempotency_key: str,
    from_address: str,
) -> dict[str, Any]:
    """Send email via AWS SES."""
    try:
        import boto3
    except ImportError:
        return {"sent": False, "error": "boto3 not installed"}

    client = boto3.client("ses", region_name="us-east-1")
    try:
        resp = client.send_email(
            Source=from_address,
            Destination={"ToAddresses": [to_address]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            },
        )
        message_id = resp["MessageId"]
        logger.info("Email sent via SES: %s -> %s", idempotency_key, to_address)
        return {
            "sent": True,
            "provider": "ses",
            "message_id": message_id,
            "idempotency_key": idempotency_key,
        }
    except Exception as exc:
        logger.error("SES send failed: %s", exc)
        return {
            "sent": False,
            "provider": "ses",
            "error": str(exc),
            "idempotency_key": idempotency_key,
        }
