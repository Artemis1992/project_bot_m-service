"""Client for approvals_service integration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class ApprovalsClient:
    """Client for starting approval chains via approvals_service."""

    def __init__(self):
        self.base_url = os.getenv("APPROVALS_SERVICE_URL", "http://approvals_service:8002/api").rstrip("/")
        self.timeout = float(os.getenv("APPROVALS_SERVICE_TIMEOUT", "15.0"))
        self.enabled = os.getenv("APPROVALS_SERVICE_ENABLED", "true").lower() == "true"

    async def start_approval_chain_async(self, request_id: int, summary: str) -> Dict[str, Any] | None:
        """
        Start approval chain for a request asynchronously.
        Returns None if disabled or on error (logs error).
        """
        if not self.enabled:
            return None

        try:
            payload = {
                "request_id": request_id,
                "summary": summary,
            }
            url = f"{self.base_url}/approvals/start"
            headers = get_api_headers()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to start approval chain for request {request_id}: {exc}")
            return None

    def start_approval_chain_sync(self, request_id: int, summary: str) -> Dict[str, Any] | None:
        """
        Synchronous wrapper for start_approval_chain_async.
        Uses asyncio.run for Django views.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.start_approval_chain_async(request_id, summary))

    async def get_approval_chain_async(self, request_id: int) -> Dict[str, Any] | None:
        """Get approval chain status for a request."""
        if not self.enabled:
            return None

        try:
            url = f"{self.base_url}/approvals/{request_id}/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to get approval chain for request {request_id}: {exc}")
            return None


# Singleton instance
_approvals_client = None


def get_approvals_client() -> ApprovalsClient:
    """Get singleton approvals client instance."""
    global _approvals_client
    if _approvals_client is None:
        _approvals_client = ApprovalsClient()
    return _approvals_client

