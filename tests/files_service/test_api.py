"""Tests for files_service API."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock

import pytest

# Add service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "files_service"))

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


class TestFilesAPI:
    def test_health_endpoint_no_auth(self, client):
        """Test health endpoint doesn't require auth."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_upload_file_without_auth_fails(self, client):
        """Test that uploading file without API key fails."""
        payload = {
            "telegram_file_id": "test_file_id",
            "file_name": "test.pdf",
            "warehouse": "Алматы",
            "category": "Авто",
            "subcategory": "Ремонт",
            "author_id": 12345,
        }
        response = client.post("/files/from-telegram", json=payload)
        assert response.status_code == 401

    def test_upload_file_with_auth(self, client, api_key):
        """Test uploading file with valid API key."""
        with patch.dict(os.environ, {"SERVICE_API_KEY": api_key}):
            with patch("main.DOWNLOADER") as mock_downloader, \
                 patch("main.STORAGE") as mock_storage:
                # Mock downloader
                mock_downloader.download_file = AsyncMock(return_value="/tmp/test.pdf")
                
                # Mock storage
                mock_storage.upload = AsyncMock(return_value="https://drive.google.com/file.pdf")
                
                payload = {
                    "telegram_file_id": "test_file_id",
                    "file_name": "test.pdf",
                    "warehouse": "Алматы",
                    "category": "Авто",
                    "subcategory": "Ремонт",
                    "author_id": 12345,
                }
                
                response = client.post(
                    "/files/from-telegram",
                    json=payload,
                    headers={"X-API-Key": api_key},
                )
                
                assert response.status_code == 200
                assert "file_url" in response.json()
                assert "storage_path" in response.json()
                assert "file_name" in response.json()

    def test_build_storage_path(self):
        """Test build_storage_path function."""
        from main import build_storage_path
        
        path = build_storage_path("Авто", "Ремонт авто", "file.pdf")
        assert "Авто" in path or "_" in path  # Normalized
        assert "file.pdf" in path
        assert len(path) > 0

