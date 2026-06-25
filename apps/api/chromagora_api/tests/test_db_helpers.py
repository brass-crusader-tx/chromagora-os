"""Tests for database helper functions."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from chromagora_api.core.supabase import is_supabase_configured


class TestDatabaseHelpers:
    """Test database helper operations."""

    def test_settings_without_supabase(self):
        """Settings should report Supabase not configured when no env vars."""
        with patch("chromagora_api.core.supabase.settings") as mock_settings:
            mock_settings.supabase_url = ""
            mock_settings.supabase_anon_key = ""
            result = is_supabase_configured()
            assert result is False

    def test_settings_with_supabase_url_only(self):
        """Supabase should not be configured with only URL (no key)."""
        with patch("chromagora_api.core.supabase.settings") as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_anon_key = ""
            result = is_supabase_configured()
            assert result is False
