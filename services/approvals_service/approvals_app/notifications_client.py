"""Client for sending notifications via bot_gateway."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class NotificationsClient:
    """Client for sending notifications through bot_gateway webhook."""

    def __init__(self):
        self.base_url = os.getenv("BOT_GATEWAY_URL", "http://bot_gateway:8003").rstrip("/")
        self.timeout = float(os.getenv("NOTIFICATIONS_TIMEOUT", "10.0"))
        self.enabled = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"

    async def notify_approver_async(
        self,
        telegram_username: str | None,
        request_id: int,
        summary: str,
        step_order: int,
        approver_name: str,
    ) -> Dict[str, Any] | None:
        """Send notification to approver."""
        if not self.enabled or not telegram_username:
            return None

        try:
            payload = {
                "type": "approver_notification",
                "telegram_username": telegram_username,
                "request_id": request_id,
                "summary": summary,
                "step_order": step_order,
                "approver_name": approver_name,
            }
            url = f"{self.base_url}/notifications/send"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to send notification: {exc}")
            return None

    async def notify_author_approved_async(self, request_id: int) -> Dict[str, Any] | None:
        """Notify author that request was approved."""
        if not self.enabled:
            return None

        try:
            payload = {
                "type": "request_approved",
                "request_id": request_id,
            }
            url = f"{self.base_url}/notifications/send"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to send approval notification: {exc}")
            return None

    async def notify_author_rejected_async(
        self, request_id: int, comment: str | None = None
    ) -> Dict[str, Any] | None:
        """Notify author that request was rejected."""
        if not self.enabled:
            return None

        try:
            payload = {
                "type": "request_rejected",
                "request_id": request_id,
                "comment": comment,
            }
            url = f"{self.base_url}/notifications/send"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to send rejection notification: {exc}")
            return None


# Singleton instance
_notifications_client = None


def get_notifications_client() -> NotificationsClient:
    """Get singleton notifications client instance."""
    global _notifications_client
    if _notifications_client is None:
        _notifications_client = NotificationsClient()
    return _notifications_client






