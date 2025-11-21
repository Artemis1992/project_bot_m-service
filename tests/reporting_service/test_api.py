"""Tests for reporting_service API."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "reporting_service"))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Get API key."""
    return "test-api-key"


class TestReportingAPI:
    def test_health_endpoint_no_auth(self, client):
        """Test health endpoint doesn't require auth."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_append_request_without_auth_fails(self, client):
        """Test that appending request without API key fails."""
        payload = {
            "request_id": 1,
            "amount": 1000.0,
            "status": "new",
        }
        response = client.post("/reports/requests", json=payload)
        assert response.status_code == 401

    def test_append_request_with_auth(self, client, api_key):
        """Test appending request with valid API key."""
        with patch.dict(os.environ, {"SERVICE_API_KEY": api_key}):
            with patch("main.writer") as mock_writer:
                mock_writer.append_request = AsyncMock(return_value="A1")
                
                payload = {
                    "request_id": 1,
                    "goal": "Test goal",
                    "item_name": "Test item",
                    "quantity": "1",
                    "amount": 1000.0,
                    "comment": "Test comment",
                    "status": "new",
                    "history": "Test history",
                }
                
                response = client.post(
                    "/reports/requests",
                    json=payload,
                    headers={"X-API-Key": api_key},
                )
                
                assert response.status_code == 200
                assert "detail" in response.json()
                assert "google_row_id" in response.json()

