"""Tests for inter-service clients."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock

import pytest
import httpx

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "requests_service"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_requests.settings")

import django
django.setup()

pytestmark = pytest.mark.django_db

from requests_app.approvals_client import ApprovalsClient, get_approvals_client
from requests_app.reporting_client import ReportingClient, get_reporting_client


@pytest.fixture
def mock_request():
    """Create a mock Request object."""
    from unittest.mock import Mock
    request = Mock()
    request.id = 1
    request.goal = "Test goal"
    request.item_name = "Test item"
    request.quantity = "1"
    request.amount = 1000.00
    request.comment = "Test comment"
    request.status = "new"
    request.current_level = 0
    request.created_at = "2024-01-01T00:00:00Z"
    request.author_full_name = "Test User"
    request.author_username = "test_user"
    request.get_status_display = Mock(return_value="Новая")
    return request


class TestApprovalsClient:
    def test_get_approvals_client_singleton(self):
        """Test that get_approvals_client returns singleton."""
        client1 = get_approvals_client()
        client2 = get_approvals_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_start_approval_chain_disabled(self):
        """Test that disabled client returns None."""
        with patch.dict(os.environ, {"APPROVALS_SERVICE_ENABLED": "false"}):
            client = ApprovalsClient()
            result = await client.start_approval_chain_async(1, "Test summary")
            assert result is None

    @pytest.mark.asyncio
    async def test_start_approval_chain_success(self):
        """Test successful approval chain start."""
        with patch.dict(os.environ, {"APPROVALS_SERVICE_ENABLED": "true", "APPROVALS_SERVICE_URL": "http://test"}):
            client = ApprovalsClient()
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = AsyncMock()
                mock_response.json.return_value = {"id": 1, "status": "pending"}
                mock_response.raise_for_status = Mock()
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                result = await client.start_approval_chain_async(1, "Test summary")
                assert result is not None
                assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_start_approval_chain_error_handling(self):
        """Test error handling in approval chain start."""
        with patch.dict(os.environ, {"APPROVALS_SERVICE_ENABLED": "true", "APPROVALS_SERVICE_URL": "http://test"}):
            client = ApprovalsClient()
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.RequestError("Connection error")
                
                result = await client.start_approval_chain_async(1, "Test summary")
                assert result is None


class TestReportingClient:
    def test_get_reporting_client_singleton(self):
        """Test that get_reporting_client returns singleton."""
        client1 = get_reporting_client()
        client2 = get_reporting_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_report_request_disabled(self, mock_request):
        """Test that disabled client returns None."""
        with patch.dict(os.environ, {"REPORTING_SERVICE_ENABLED": "false"}):
            client = ReportingClient()
            result = await client.report_request_async(mock_request)
            assert result is None

    @pytest.mark.asyncio
    async def test_report_request_success(self, mock_request):
        """Test successful request reporting."""
        with patch.dict(os.environ, {"REPORTING_SERVICE_ENABLED": "true", "REPORTING_SERVICE_URL": "http://test"}):
            client = ReportingClient()
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = AsyncMock()
                mock_response.json.return_value = {"google_row_id": "A1"}
                mock_response.raise_for_status = Mock()
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                result = await client.report_request_async(mock_request)
                assert result is not None
                assert result["google_row_id"] == "A1"

    def test_build_history(self, mock_request):
        """Test history building."""
        with patch.dict(os.environ, {"REPORTING_SERVICE_ENABLED": "true"}):
            client = ReportingClient()
            history = client._build_history(mock_request)
            assert "Создано" in history
            assert "Автор" in history
            assert "Статус" in history

