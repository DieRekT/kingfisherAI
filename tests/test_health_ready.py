"""Tests for health and ready endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


@pytest.fixture
def client():
    """Create test client."""
    from apps.api.main import app
    return TestClient(app)


def test_health(client):
    """Test /health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "app" in data


@pytest.mark.asyncio
async def test_ready_healthy(client):
    """Test /ready endpoint when upstream is healthy."""
    with patch("apps.api.main.AsyncOpenAI") as mock_openai:
        # Mock successful upstream check
        mock_client = AsyncMock()
        mock_client.models.list = AsyncMock(return_value=[])
        mock_openai.return_value = mock_client
        
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["upstream"] == "healthy"


@pytest.mark.asyncio
async def test_ready_unhealthy(client):
    """Test /ready endpoint when upstream is down."""
    with patch("apps.api.main.AsyncOpenAI") as mock_openai:
        # Mock upstream failure
        mock_client = AsyncMock()
        mock_client.models.list = AsyncMock(side_effect=Exception("Connection failed"))
        mock_openai.return_value = mock_client
        
        response = client.get("/ready")
        assert response.status_code == 503


def test_metrics_endpoint(client):
    """Test /metrics endpoint returns Prometheus format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Check for prometheus content type
    assert "text/plain" in response.headers.get("content-type", "")

