"""Tests for email service (Chapter 22.1)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import chromagora_api.services.email_service as email_module


# ---------------------------------------------------------------------------
# Feature flag tests
# ---------------------------------------------------------------------------

def test_real_email_disabled_by_default():
    """ENABLE_REAL_EMAIL_SENDING defaults to false."""
    os.environ.pop("ENABLE_REAL_EMAIL_SENDING", None)
    import importlib
    importlib.reload(email_module)
    assert email_module.is_real_email_enabled() is False


def test_real_email_enabled_via_env():
    """ENABLE_REAL_EMAIL_SENDING=true enables the feature."""
    with patch.dict(os.environ, {"ENABLE_REAL_EMAIL_SENDING": "true"}):
        import importlib
        importlib.reload(email_module)
        assert email_module.is_real_email_enabled() is True


def test_send_email_when_disabled_returns_mock():
    """send_email returns mock result when feature is off."""
    with patch.dict(os.environ, {"ENABLE_REAL_EMAIL_SENDING": "false"}):
        import importlib
        importlib.reload(email_module)
        result = email_module.send_email(
            to_address="test@example.com",
            subject="Test",
            body="Hello",
            idempotency_key=str(uuid4()),
        )

    assert result["sent"] is False
    assert result["mock"] is True
    assert result["provider"] == "mock"


def test_send_email_when_enabled_uses_provider():
    """send_email routes to correct provider when enabled."""
    with patch.dict(os.environ, {
        "ENABLE_REAL_EMAIL_SENDING": "true",
        "EMAIL_PROVIDER": "sendgrid",
        "SENDGRID_API_KEY": "test-key",
    }):
        import importlib
        importlib.reload(email_module)

        mock_result = {
            "sent": True,
            "provider": "sendgrid",
            "message_id": "test-msg-id",
            "idempotency_key": "test-idem",
        }
        with patch("chromagora_api.services.email_provider.sendgrid_send", return_value=mock_result):
            result = email_module.send_email(
                to_address="test@example.com",
                subject="Test",
                body="Hello",
                idempotency_key="test-idem",
            )

    assert result["sent"] is True
    assert result["provider"] == "sendgrid"


def test_send_email_unknown_provider_returns_mock():
    """send_email falls back to mock for unknown provider."""
    with patch.dict(os.environ, {
        "ENABLE_REAL_EMAIL_SENDING": "true",
        "EMAIL_PROVIDER": "unknown",
    }):
        import importlib
        importlib.reload(email_module)
        result = email_module.send_email(
            to_address="test@example.com",
            subject="Test",
            body="Hello",
            idempotency_key=str(uuid4()),
        )

    assert result["sent"] is False
    assert result["provider"] == "mock"


def test_send_email_sendgrid_no_api_key():
    """SendGrid provider returns error when key not configured."""
    with patch.dict(os.environ, {
        "ENABLE_REAL_EMAIL_SENDING": "true",
        "EMAIL_PROVIDER": "sendgrid",
    }):
        import importlib
        importlib.reload(email_module)
        result = email_module.send_email(
            to_address="test@example.com",
            subject="Test",
            body="Hello",
            idempotency_key=str(uuid4()),
        )

    assert result["sent"] is False
    assert "error" in result


def test_send_email_ses_provider():
    """SES provider routes correctly."""
    with patch.dict(os.environ, {
        "ENABLE_REAL_EMAIL_SENDING": "true",
        "EMAIL_PROVIDER": "ses",
    }):
        import importlib
        importlib.reload(email_module)

        mock_result = {
            "sent": True,
            "provider": "ses",
            "message_id": "ses-msg-id",
        }
        with patch("chromagora_api.services.email_provider.ses_send", return_value=mock_result):
            result = email_module.send_email(
                to_address="test@example.com",
                subject="Test",
                body="Hello",
                idempotency_key="test-idem",
            )

    assert result["sent"] is True
    assert result["provider"] == "ses"
