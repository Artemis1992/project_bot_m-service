"""HTTP client for the requests_service."""

from __future__ import annotations

from typing import Any, Dict

import httpx
from pydantic import BaseModel


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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload.model_dump())
            response.raise_for_status()
            return response.json()

    async def attach_file(
        self,
        request_id: int,
        payload: AttachmentPayload,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/requests/{request_id}/attach/"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload.model_dump())
            response.raise_for_status()
            return response.json()

