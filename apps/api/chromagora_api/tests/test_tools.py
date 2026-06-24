"""Tests for Tool Definitions and Business Tool Permissions routes."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from chromagora_api.routes.tools import router


class TestListToolDefinitions:
    @patch("chromagora_api.routes.tools.get_supabase")
    def test_lists_active_tools(self, mock_sb):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = [
            {"id": "t1", "name": "send_email", "is_active": True},
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp
        mock_sb.return_value = mock_client

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.get(f"/businesses/{uuid4()}/tools/definitions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("chromagora_api.routes.tools.get_supabase")
    def test_no_db_returns_503(self, mock_sb):
        mock_sb.return_value = None

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.get(f"/businesses/{uuid4()}/tools/definitions")
        assert resp.status_code == 503


class TestListBusinessToolPermissions:
    @patch("chromagora_api.routes.tools.get_supabase")
    def test_lists_permissions(self, mock_sb):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp
        mock_sb.return_value = mock_client

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.get(f"/businesses/{uuid4()}/tools")
        assert resp.status_code == 200
        assert resp.json() == []


class TestEnableTool:
    @patch("chromagora_api.routes.tools.get_supabase")
    def test_enables_tool(self, mock_sb):
        mock_client = MagicMock()

        # Tool definition exists
        mock_tool_resp = MagicMock()
        mock_tool_resp.data = [{"id": "t1"}]

        # Upsert result
        mock_upsert_resp = MagicMock()
        mock_upsert_resp.data = [{"id": "p1", "is_enabled": True}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_tool_resp
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_upsert_resp

        mock_sb.return_value = mock_client

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post(
            f"/businesses/{uuid4()}/tools/{uuid4()}/enable"
        )
        assert resp.status_code == 201
        assert resp.json()["is_enabled"] is True

    @patch("chromagora_api.routes.tools.get_supabase")
    def test_tool_not_found(self, mock_sb):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp
        mock_sb.return_value = mock_client

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post(
            f"/businesses/{uuid4()}/tools/{uuid4()}/enable"
        )
        assert resp.status_code == 404


class TestDisableTool:
    @patch("chromagora_api.routes.tools.get_supabase")
    def test_disables_tool(self, mock_sb):
        mock_client = MagicMock()
        mock_upsert_resp = MagicMock()
        mock_upsert_resp.data = [{"id": "p1", "is_enabled": False}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_upsert_resp
        mock_sb.return_value = mock_client

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.post(
            f"/businesses/{uuid4()}/tools/{uuid4()}/disable"
        )
        assert resp.status_code == 200
        assert resp.json()["is_enabled"] is False


class TestUpdateToolPermission:
    @patch("chromagora_api.routes.tools.get_supabase")
    def test_updates_autonomy(self, mock_sb):
        mock_client = MagicMock()
        mock_upsert_resp = MagicMock()
        mock_upsert_resp.data = [{"id": "p1", "max_autonomy_level": 3}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_upsert_resp
        mock_sb.return_value = mock_client

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.patch(
            f"/businesses/{uuid4()}/tools/{uuid4()}",
            json={"max_autonomy_level": 3},
        )
        assert resp.status_code == 200
        assert resp.json()["max_autonomy_level"] == 3

    @patch("chromagora_api.routes.tools.get_supabase")
    def test_no_fields_returns_400(self, mock_sb):
        mock_sb.return_value = MagicMock()

        from fastapi.testclient import TestClient
        from chromagora_api.main import app
        client = TestClient(app)

        resp = client.patch(
            f"/businesses/{uuid4()}/tools/{uuid4()}",
            json={},
        )
        assert resp.status_code == 400
