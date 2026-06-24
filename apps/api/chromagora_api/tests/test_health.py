"""Tests for health and version endpoints."""

from httpx import ASGITransport, AsyncClient
import pytest

from chromagora_api.main import app


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "supabase_configured" in data


@pytest.mark.asyncio
async def test_health_returns_env(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    data = response.json()
    assert "environment" in data


@pytest.mark.asyncio
async def test_version(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"
