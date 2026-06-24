"""Tests for database helper functions."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from chromagora_api.core.config import Settings
from chromagora_api.core.supabase import is_supabase_configured


class TestDatabaseHelpers:
    """Test database helper operations."""

    def test_settings_without_supabase(self):
        """Settings should report Supabase not configured when no env vars."""
        with patch.dict("os.environ", {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""}, clear=False):
            result = is_supabase_configured()
            assert result is False

    def test_settings_with_supabase_url_only(self):
        """Supabase should not be configured with only URL (no key)."""
        with patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": ""}, clear=False):
            result = is_supabase_configured()
            assert result is False
