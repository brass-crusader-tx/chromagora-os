"""Tests for trace ID propagation (Chapter 18.1)."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from chromagora_api.services.trace_propagation import (
    ensure_trace_id,
    get_records_by_trace,
)


class TestEnsureTraceId:
    def test_generates_new_id(self):
        tid = ensure_trace_id()
        assert tid
        assert len(tid) == 36  # UUID format

    def test_returns_existing_id(self):
        existing = str(uuid4())
        tid = ensure_trace_id(existing)
        assert tid == existing

    def test_none_generates_new(self):
        tid = ensure_trace_id(None)
        assert tid
        assert len(tid) == 36

    def test_empty_string_generates_new(self):
        tid = ensure_trace_id("")
        assert tid
        assert len(tid) == 36

    def test_unique_ids(self):
        ids = {ensure_trace_id() for _ in range(100)}
        assert len(ids) == 100


class TestGetRecordsByTrace:
    def test_returns_empty_when_no_db(self):
        with patch("chromagora_api.db.base.get_supabase") as mock_sb:
            mock_sb.return_value = None
            result = get_records_by_trace("test-trace")
            assert result == {}

    def test_queries_tables(self):
        with patch("chromagora_api.db.base.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.data = None
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp
            mock_sb.return_value = mock_client

            result = get_records_by_trace("test-trace")
            assert isinstance(result, dict)
            # Should query all 13 tables
            assert mock_client.table.call_count == 13
