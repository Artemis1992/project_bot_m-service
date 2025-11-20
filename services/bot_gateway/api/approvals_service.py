"""HTTP client for the approvals_service."""

from __future__ import annotations

from typing import Any, Dict

import httpx

from .http_utils import get_api_headers
from .retry_client import retry_request


class ApprovalsServiceClient:
    """
    Клиент для работы с цепочкой согласования:
    Денис → Жасулан → Мейржан → (Лязат/Айгуль)
    """

    def __init__(self, base_url: str, *, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def start_approval_chain(self, request_id: int, summary: str) -> Dict[str, Any]:
        """Запустить цепочку согласования."""
        url = f"{self.base_url}/approvals/start"
        headers = get_api_headers()
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"request_id": request_id, "summary": summary},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

    async def approve_request(
        self,
        request_id: int,
        actor_username: str | None = None,
        comment: str | None = None
    ) -> Dict[str, Any]:
        """Одобрить заявку на текущем шаге."""
        url = f"{self.base_url}/approvals/{request_id}/approve"
        headers = get_api_headers()
        
        payload: Dict[str, Any] = {}
        if actor_username:
            payload["actor_username"] = actor_username
        if comment:
            payload["comment"] = comment
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

    async def reject_request(
        self,
        request_id: int,
        comment: str | None = None,
        actor_username: str | None = None
    ) -> Dict[str, Any]:
        """Отклонить заявку на текущем шаге."""
        url = f"{self.base_url}/approvals/{request_id}/reject"
        headers = get_api_headers()
        
        payload: Dict[str, Any] = {}
        if actor_username:
            payload["actor_username"] = actor_username
        if comment:
            payload["comment"] = comment
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

    async def get_approval_chain(self, request_id: int) -> Dict[str, Any]:
        """Получить информацию о цепочке согласования."""
        url = f"{self.base_url}/approvals/{request_id}/"
        headers = get_api_headers()
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

