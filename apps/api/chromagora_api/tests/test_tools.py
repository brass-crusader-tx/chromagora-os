"""Tests for Tool Definitions and Business Tool Permissions routes."""

from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from chromagora_api.main import app

# Create client once at module level to avoid re-creating per test
_client = TestClient(app)


def _stub_tools(mock_sb):
    """Patch _scoped_client to return mock_sb and return the patcher."""
    return patch("chromagora_api.routes.tools._scoped_client", return_value=mock_sb)


class TestListToolDefinitions:
    def test_lists_active_tools(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = [{"id": "t1", "name": "send_email", "is_active": True}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp

        with _stub_tools(mock_client):
            resp = _client.get(f"/businesses/{uuid4()}/tools/definitions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_no_db_returns_503(self):
        with patch("chromagora_api.routes.tools.get_supabase", return_value=None):
            resp = _client.get(f"/businesses/{uuid4()}/tools/definitions")
        assert resp.status_code == 503


class TestListBusinessToolPermissions:
    def test_lists_permissions(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp

        with _stub_tools(mock_client):
            resp = _client.get(f"/businesses/{uuid4()}/tools")
        assert resp.status_code == 200
        assert resp.json() == []


class TestEnableTool:
    def test_enables_tool(self):
        mock_client = MagicMock()
        mock_tool_resp = MagicMock()
        mock_tool_resp.data = [{"id": "t1"}]
        mock_upsert_resp = MagicMock()
        mock_upsert_resp.data = [{"id": "p1", "is_enabled": True}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_tool_resp
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_upsert_resp

        with _stub_tools(mock_client):
            resp = _client.post(f"/businesses/{uuid4()}/tools/{uuid4()}/enable")
        assert resp.status_code == 201
        assert resp.json()["is_enabled"] is True

    def test_tool_not_found(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp

        with _stub_tools(mock_client):
            resp = _client.post(f"/businesses/{uuid4()}/tools/{uuid4()}/enable")
        assert resp.status_code == 404


class TestDisableTool:
    def test_disables_tool(self):
        mock_client = MagicMock()
        mock_upsert_resp = MagicMock()
        mock_upsert_resp.data = [{"id": "p1", "is_enabled": False}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_upsert_resp

        with _stub_tools(mock_client):
            resp = _client.post(f"/businesses/{uuid4()}/tools/{uuid4()}/disable")
        assert resp.status_code == 200
        assert resp.json()["is_enabled"] is False


class TestUpdateToolPermission:
    def test_updates_autonomy(self):
        mock_client = MagicMock()
        mock_upsert_resp = MagicMock()
        mock_upsert_resp.data = [{"id": "p1", "max_autonomy_level": 3}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_upsert_resp

        with _stub_tools(mock_client):
            resp = _client.patch(
                f"/businesses/{uuid4()}/tools/{uuid4()}",
                json={"max_autonomy_level": 3},
            )
        assert resp.status_code == 200
        assert resp.json()["max_autonomy_level"] == 3

    def test_no_fields_returns_400(self):
        with patch("chromagora_api.routes.tools.get_supabase", return_value=MagicMock()):
            resp = _client.patch(
                f"/businesses/{uuid4()}/tools/{uuid4()}",
                json={},
            )
        assert resp.status_code == 400
