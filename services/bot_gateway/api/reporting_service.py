"""HTTP client for the reporting_service."""

from __future__ import annotations

from typing import Any, Dict

import httpx
from pydantic import BaseModel

from .http_utils import get_api_headers
from .retry_client import retry_request


class RequestReport(BaseModel):
    request_id: int
    goal: str | None = None
    item_name: str | None = None
    quantity: str | None = None
    amount: float
    comment: str | None = None
    status: str
    history: str | None = None


class ReportingServiceClient:
    """
    Client for sending request reports to reporting_service.
    """

    def __init__(self, base_url: str, *, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def report_request(self, report: RequestReport) -> Dict[str, Any]:
        """
        Send request report to reporting service.
        """
        url = f"{self.base_url}/reports/requests"
        headers = get_api_headers()

        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=report.model_dump(), headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

