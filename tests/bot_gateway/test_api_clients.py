"""Tests for bot_gateway API clients."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import httpx

# Add service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "bot_gateway"))

from api.requests_service import RequestsServiceClient, RequestPayload
from api.categories_service import CategoriesServiceClient
from api.files_service import FilesServiceClient
from api.reporting_service import ReportingServiceClient, RequestReport
from api.retry_client import retry_request


class TestRequestsServiceClient:
    @pytest.mark.asyncio
    async def test_create_request_success(self):
        """Test successful request creation."""
        client = RequestsServiceClient("http://test")
        payload = RequestPayload(
            tg_user_id=12345,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт",
            amount=1000.0,
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"id": 1, "status": "new"}
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await client.create_request(payload)
            assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_create_request_retry(self):
        """Test request creation with retry."""
        client = RequestsServiceClient("http://test")
        payload = RequestPayload(
            tg_user_id=12345,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт",
            amount=1000.0,
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            # First call fails, second succeeds
            mock_response_success = AsyncMock()
            mock_response_success.json.return_value = {"id": 1}
            mock_response_success.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post.side_effect = [
                httpx.RequestError("Connection error"),
                mock_response_success,
            ]
            
            result = await client.create_request(payload)
            assert result["id"] == 1


class TestCategoriesServiceClient:
    @pytest.mark.asyncio
    async def test_fetch_structure_success(self):
        """Test successful structure fetch."""
        client = CategoriesServiceClient("http://test")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = [
                {
                    "id": "almaty",
                    "name": "Алматы",
                    "categories": [
                        {
                            "id": "auto",
                            "name": "Авто",
                            "subcategories": [
                                {"id": "repair", "name": "Ремонт"}
                            ],
                        }
                    ],
                }
            ]
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await client.fetch_structure()
            assert len(result) == 1
            assert result[0].id == "almaty"
            assert len(result[0].categories) == 1


class TestRetryClient:
    @pytest.mark.asyncio
    async def test_retry_success_after_failure(self):
        """Test retry succeeds after initial failure."""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.RequestError("Connection error")
            return {"success": True}
        
        result = await retry_request(failing_func, max_retries=3)
        assert result["success"] is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry exhausts after max attempts."""
        async def always_failing():
            raise httpx.RequestError("Connection error")
        
        with pytest.raises(httpx.RequestError):
            await retry_request(always_failing, max_retries=2)

