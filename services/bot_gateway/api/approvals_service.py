"""Placeholder client for approvals workflow (future steps)."""

from __future__ import annotations

import httpx


class ApprovalsServiceClient:
    """
    Позже будем использовать для запуска цепочки согласования:
    Денис → Жасулан → Мейржан → (Лязат/Айгуль)
    """

    def __init__(self, base_url: str, *, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def notify_new_request(self, request_id: int) -> None:
        url = f"{self.base_url}/approvals/start"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json={"request_id": request_id})
            response.raise_for_status()

