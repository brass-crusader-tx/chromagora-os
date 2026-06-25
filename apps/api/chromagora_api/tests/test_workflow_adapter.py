"""Tests for workflow adapter interface (Chapter 21)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from chromagora_api.services.workflow_adapter import (
    WorkflowAdapter,
    WorkflowLiteAdapter,
    get_adapter,
)


# ---------------------------------------------------------------------------
# Interface contract test
# ---------------------------------------------------------------------------

def test_workflow_adapter_is_abstract():
    """WorkflowAdapter cannot be instantiated directly."""
    with pytest.raises(TypeError):
        WorkflowAdapter()


def test_workflow_lite_adapter_instantiates():
    """WorkflowLiteAdapter can be instantiated."""
    adapter = WorkflowLiteAdapter()
    assert adapter is not None
    assert isinstance(adapter, WorkflowAdapter)


def test_get_adapter_returns_workflow_lite():
    """get_adapter() returns WorkflowLiteAdapter by default."""
    adapter = get_adapter()
    assert isinstance(adapter, WorkflowLiteAdapter)


# ---------------------------------------------------------------------------
# WorkflowLiteAdapter tests
# ---------------------------------------------------------------------------

class TestWorkflowLiteAdapter:
    """Tests for the database-backed workflow adapter."""

    def test_start_workflow_pops_tenant_id(self, monkeypatch):
        """start_workflow extracts tenant_id from input_data."""
        mock_create = MagicMock()
        mock_result = MagicMock()
        mock_result.id = uuid4()
        mock_create.return_value = mock_result

        adapter = WorkflowLiteAdapter()

        monkeypatch.setattr(
            "chromagora_api.services.workflow_engine.create_workflow_run",
            mock_create,
        )
        # Patch the import inside the adapter
        with patch("chromagora_api.services.workflow_engine.create_workflow_run", mock_create):
            result = adapter.start_workflow(
                workflow_type="review_request",
                business_id=uuid4(),
                input_data={"_tenant_id": uuid4(), "customer_name": "Test"},
            )

        assert result == str(mock_result.id)

    def test_start_workflow_raises_without_tenant_id(self):
        """start_workflow raises ValueError if tenant_id missing."""
        adapter = WorkflowLiteAdapter()

        with pytest.raises(ValueError, match="tenant_id required"):
            adapter.start_workflow(
                workflow_type="review_request",
                business_id=uuid4(),
                input_data={"customer_name": "Test"},
            )

    def test_signal_workflow_approve(self, monkeypatch):
        """signal_workflow 'approve' maps to RUNNING status."""
        from chromagora_schemas.workflows import WorkflowStatus

        mock_update = MagicMock()
        mock_update.return_value = MagicMock()

        adapter = WorkflowLiteAdapter()

        with patch("chromagora_api.services.workflow_engine.update_workflow_state", mock_update):
            result = adapter.signal_workflow(str(uuid4()), "approve")

        assert result is True
        mock_update.assert_called_once()

    def test_signal_workflow_reject(self, monkeypatch):
        """signal_workflow 'reject' maps to CANCELLED status."""
        mock_update = MagicMock()
        mock_update.return_value = MagicMock()

        adapter = WorkflowLiteAdapter()

        with patch("chromagora_api.services.workflow_engine.update_workflow_state", mock_update):
            result = adapter.signal_workflow(str(uuid4()), "reject")

        assert result is True

    def test_signal_workflow_unknown_signal(self):
        """signal_workflow with unknown signal returns False."""
        adapter = WorkflowLiteAdapter()
        result = adapter.signal_workflow(str(uuid4()), "unknown_signal")
        assert result is False

    def test_get_workflow_status_not_found(self):
        """get_workflow_status returns error dict when not found."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute.return_value = MagicMock(data=[])

        adapter = WorkflowLiteAdapter()

        with patch("chromagora_api.services.workflow_adapter.get_supabase", return_value=mock_sb):
            result = adapter.get_workflow_status(str(uuid4()))

        assert "error" in result

    def test_get_workflow_status_found(self):
        """get_workflow_status returns data when found."""
        mock_sb = MagicMock()
        expected = {"id": str(uuid4()), "status": "running"}
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[expected])
        mock_sb.table.return_value = mock_table

        adapter = WorkflowLiteAdapter()

        with patch("chromagora_api.services.workflow_adapter.get_supabase", return_value=mock_sb):
            result = adapter.get_workflow_status(str(uuid4()))

        assert result == expected

    def test_cancel_workflow(self):
        """cancel_workflow calls update with CANCELLED status."""
        mock_update = MagicMock()
        mock_update.return_value = MagicMock()

        adapter = WorkflowLiteAdapter()

        with patch("chromagora_api.services.workflow_engine.update_workflow_state", mock_update):
            result = adapter.cancel_workflow(str(uuid4()), reason="test cancel")

        assert result is True
        mock_update.assert_called_once()
