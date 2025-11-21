"""Client for reporting_service integration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

from .http_utils import get_api_headers

logger = logging.getLogger(__name__)


class ReportingClient:
    """Client for sending request updates to reporting_service."""

    def __init__(self):
        self.base_url = os.getenv("REPORTING_SERVICE_URL", "http://reporting_service:8200").rstrip("/")
        self.timeout = float(os.getenv("REPORTING_SERVICE_TIMEOUT", "15.0"))
        self.enabled = os.getenv("REPORTING_SERVICE_ENABLED", "true").lower() == "true"

    async def report_request_async(self, request_obj: "Request") -> Dict[str, Any] | None:
        """
        Send request report to reporting service asynchronously.
        Returns None if disabled or on error (logs error).
        """
        if not self.enabled:
            return None

        try:
            history = self._build_history(request_obj)
            payload = {
                "request_id": request_obj.id,
                "goal": request_obj.goal or None,
                "item_name": request_obj.item_name or None,
                "quantity": request_obj.quantity or None,
                "amount": float(request_obj.amount),
                "comment": request_obj.comment or None,
                "status": request_obj.status,
                "history": history,
            }
            url = f"{self.base_url}/reports/requests"
            headers = get_api_headers()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                # Сохраняем google_row_id если вернулся
                if "google_row_id" in result:
                    request_obj.google_row_id = result["google_row_id"]
                    request_obj.save(update_fields=["google_row_id"])
                return result
        except Exception as exc:
            logger.error(f"Failed to report request {request_obj.id} to reporting_service: {exc}")
            return None

    def report_request_sync(self, request_obj: "Request") -> Dict[str, Any] | None:
        """
        Synchronous wrapper for report_request_async.
        Uses asyncio.run for Django views.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.report_request_async(request_obj))

    def _build_history(self, request_obj: "Request") -> str:
        """Build history string from request data."""
        parts = [
            f"Создано: {request_obj.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Автор: {request_obj.author_full_name or request_obj.author_username or 'N/A'}",
            f"Статус: {request_obj.get_status_display()}",
        ]
        if request_obj.current_level > 0:
            parts.append(f"Уровень согласования: {request_obj.current_level}")
        return " | ".join(parts)


# Singleton instance
_reporting_client = None


def get_reporting_client() -> ReportingClient:
    """Get singleton reporting client instance."""
    global _reporting_client
    if _reporting_client is None:
        _reporting_client = ReportingClient()
    return _reporting_client

