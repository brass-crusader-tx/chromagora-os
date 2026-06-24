"""Tests for configuration."""

import os
from unittest.mock import patch

from chromagora_api.core.config import Settings


def test_default_settings():
    with patch.dict(os.environ, {}, clear=False):
        s = Settings(_env_file=None)
        assert s.api_host == "127.0.0.1"
        assert s.api_port == 8000
        assert s.version == "0.1.0"
        assert s.chromagora_env == "development"


def test_env_override():
    with patch.dict(
        os.environ,
        {
            "API_PORT": "9000",
            "CHROMAGORA_ENV": "testing",
            "VERSION": "0.2.0",
        },
    ):
        s = Settings(_env_file=None)
        assert s.api_port == 9000
        assert s.chromagora_env == "testing"
        assert s.version == "0.2.0"
