"""Tests for vector memory service (Chapter 20.3)."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Ensure the service module uses our env patch
import chromagora_api.services.vector_memory as vm_module

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_supabase(data=None, insert_data=None):
    mock_sb = MagicMock()
    table_mock = MagicMock()
    if data is not None:
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.in_.return_value = table_mock
        table_mock.order.return_value = table_mock
        table_mock.limit.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=data)
    elif insert_data is not None:
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=insert_data)
    mock_sb.table.return_value = table_mock
    return mock_sb, table_mock


# ---------------------------------------------------------------------------
# Feature flag tests
# ---------------------------------------------------------------------------

def test_vector_memory_disabled_by_default():
    """ENABLE_VECTOR_MEMORY defaults to false."""
    # Ensure env is clean
    os.environ.pop("ENABLE_VECTOR_MEMORY", None)
    # Reload module to pick up env change
    import importlib
    importlib.reload(vm_module)
    assert vm_module.is_vector_memory_enabled() is False


def test_vector_memory_enabled_via_env():
    """ENABLE_VECTOR_MEMORY=true enables the feature."""
    with patch.dict(os.environ, {"ENABLE_VECTOR_MEMORY": "true"}):
        import importlib
        importlib.reload(vm_module)
        assert vm_module.is_vector_memory_enabled() is True


def test_store_embedding_when_disabled_returns_none():
    """store_embedding returns None when feature is off."""
    with patch.dict(os.environ, {"ENABLE_VECTOR_MEMORY": "false"}):
        import importlib
        importlib.reload(vm_module)
        result = vm_module.store_artifact(uuid4(), [0.1, 0.2])
    assert result is None


def test_similarity_search_when_disabled_returns_empty():
    """similarity_search returns [] when feature is off."""
    with patch.dict(os.environ, {"ENABLE_VECTOR_MEMORY": "false"}):
        import importlib
        importlib.reload(vm_module)
        result = vm_module.similarity_search(uuid4(), [0.1, 0.2])
    assert result == []


# ---------------------------------------------------------------------------
# Memory artifact CRUD (works regardless of feature flag)
# ---------------------------------------------------------------------------

def test_create_artifact_inserts_record():
    """create_artifact inserts a row into memory_artifacts."""
    inserted = {"id": str(uuid4()), "artifact_type": "note", "title": "Test"}
    mock_sb, table_mock = _mock_supabase(insert_data=[inserted])

    with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
        result = vm_module.create_artifact(
            business_id=uuid4(),
            title="Test note",
            text_content="Test content",
            artifact_type="note",
        )

    assert result["id"] == inserted["id"]
    mock_sb.table.assert_called_with("memory_artifacts")


def test_list_artifacts_returns_list():
    """list_artifacts returns filtered results."""
    data = [
        {"id": str(uuid4()), "title": "A", "artifact_type": "note"},
        {"id": str(uuid4()), "title": "B", "artifact_type": "note"},
    ]
    mock_sb, _ = _mock_supabase(data=data)

    with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
        result = vm_module.list_artifacts(uuid4())

    assert len(result) == 2


def test_list_artifacts_empty():
    """list_artifacts returns [] when no data."""
    mock_sb, _ = _mock_supabase(data=[])

    with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
        result = vm_module.list_artifacts(uuid4())

    assert result == []


def test_delete_artifact_deletes_record():
    """delete_artifact removes the row."""
    mock_sb = MagicMock()
    table_mock = MagicMock()
    table_mock.delete.return_value = table_mock
    table_mock.eq.return_value = table_mock
    mock_sb.table.return_value = table_mock
    mock_execute = MagicMock(data=[{"id": str(uuid4())}])
    table_mock.execute.return_value = mock_execute

    with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
        result = vm_module.delete_artifact(uuid4())

    assert result is True


def test_delete_artifact_with_vector_enabled_also_deletes_embeddings():
    """delete_artifact cascades to embeddings when feature is on."""
    with patch.dict(os.environ, {"ENABLE_VECTOR_MEMORY": "true"}):
        import importlib
        importlib.reload(vm_module)

        mock_sb = MagicMock()
        artifact_table = MagicMock()
        embedding_table = MagicMock()
        embedding_table.delete.return_value = embedding_table
        embedding_table.eq.return_value = embedding_table

        def table_router(name):
            if name == "memory_artifacts":
                return artifact_table
            if name == "memory_embeddings":
                return embedding_table
            return MagicMock()

        mock_sb.table.side_effect = table_router

        with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
            result = vm_module.delete_artifact(uuid4())

        # Embeddings table was queried for deletion
        mock_sb.table.assert_any_call("memory_embeddings")
        assert result is True


# ---------------------------------------------------------------------------
# Embedding tests (feature ON)
# ---------------------------------------------------------------------------

def test_store_embedding_when_enabled():
    """store_embedding inserts into memory_embeddings when feature is on."""
    with patch.dict(os.environ, {"ENABLE_VECTOR_MEMORY": "true"}):
        import importlib
        importlib.reload(vm_module)

        inserted = {"id": str(uuid4()), "embedding_model": "text-embedding-3-small"}
        mock_sb, table_mock = _mock_supabase(insert_data=[inserted])

        with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
            result = vm_module.store_artifact(
                artifact_fk=uuid4(),
                embedding_vector=[0.1] * 1536,
            )

        assert result is not None
        mock_sb.table.assert_called_with("memory_embeddings")


def test_similarity_search_when_enabled_calls_rpc():
    """similarity_search uses Supabase RPC when feature is on."""
    with patch.dict(os.environ, {"ENABLE_VECTOR_MEMORY": "true"}):
        import importlib
        importlib.reload(vm_module)

        mock_sb = MagicMock()
        mock_sb.rpc.return_value = MagicMock(data=[{"id": str(uuid4()), "similarity": 0.9}])

        with patch.object(vm_module, "_get_supabase", return_value=mock_sb):
            result = vm_module.similarity_search(uuid4(), [0.1] * 1536, top_k=5)

        assert len(result) == 1
        assert result[0]["similarity"] == 0.9
        mock_sb.rpc.assert_called_once()
