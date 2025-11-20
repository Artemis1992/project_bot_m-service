"""HTTP client for the requests_service."""

from __future__ import annotations

from typing import Any, Dict

import httpx
from pydantic import BaseModel

from .http_utils import get_api_headers
from .retry_client import retry_request


class RequestPayload(BaseModel):
    tg_user_id: int
    author_username: str | None = None
    author_full_name: str | None = None
    warehouse: str
    category: str
    subcategory: str
    subsubcategory: str | None = None
    extra_value: str | None = None
    goal: str | None = None
    item_name: str | None = None
    quantity: str | None = None
    amount: float
    comment: str | None = None


class AttachmentPayload(BaseModel):
    file_url: str
    storage_path: str
    file_name: str


class RequestsServiceClient:
    """
    Minimal wrapper around requests_service REST API.

    The URLs follow the schema:
        POST {base_url}/requests/        -> create request
        GET  {base_url}/requests/{id}/  -> retrieve request
        PATCH {base_url}/requests/{id}/ -> update request
        POST {base_url}/requests/{id}/attach/ -> add file
    """

    def __init__(self, base_url: str, *, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def create_request(self, payload: RequestPayload) -> Dict[str, Any]:
        url = f"{self.base_url}/requests/"
        headers = get_api_headers()

        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload.model_dump(), headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

    async def attach_file(
        self,
        request_id: int,
        payload: AttachmentPayload,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/requests/{request_id}/attach/"
        headers = get_api_headers()

        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload.model_dump(), headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

    async def get_user_requests(self, tg_user_id: int) -> list[Dict[str, Any]]:
        """Получить список заявок пользователя."""
        url = f"{self.base_url}/requests/"
        headers = get_api_headers()
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"tg_user_id": tg_user_id}
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

    async def get_request(self, request_id: int) -> Dict[str, Any]:
        """Получить детальную информацию о заявке."""
        url = f"{self.base_url}/requests/{request_id}/"
        headers = get_api_headers()

        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        return await retry_request(_make_request)

