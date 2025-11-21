"""Client for requests_service integration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx


def get_api_headers() -> Dict[str, str]:
    """Get headers with API key for inter-service requests."""
    api_key = os.getenv("SERVICE_API_KEY")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    return headers

logger = logging.getLogger(__name__)


class RequestsClient:
    """Client for updating request status in requests_service."""

    def __init__(self):
        self.base_url = os.getenv("REQUESTS_SERVICE_URL", "http://requests_service:8000/api").rstrip("/")
        self.timeout = float(os.getenv("REQUESTS_SERVICE_TIMEOUT", "15.0"))
        self.enabled = os.getenv("REQUESTS_SERVICE_ENABLED", "true").lower() == "true"

    async def update_request_status_async(
        self, request_id: int, status: str, current_level: int = 0
    ) -> Dict[str, Any] | None:
        """
        Update request status in requests_service asynchronously.
        """
        if not self.enabled:
            return None

        try:
            payload = {
                "status": status,
                "current_level": current_level,
            }
            url = f"{self.base_url}/requests/{request_id}/"
            headers = get_api_headers()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to update request {request_id} status: {exc}")
            return None

    def update_request_status_sync(
        self, request_id: int, status: str, current_level: int = 0
    ) -> Dict[str, Any] | None:
        """Synchronous wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.update_request_status_async(request_id, status, current_level))


# Singleton instance
_requests_client = None


def get_requests_client() -> RequestsClient:
    """Get singleton requests client instance."""
    global _requests_client
    if _requests_client is None:
        _requests_client = RequestsClient()
    return _requests_client

