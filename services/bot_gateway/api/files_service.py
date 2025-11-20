"""Client responsible for delegating uploads to files_service."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from .http_utils import get_api_headers
from .retry_client import retry_request


class FileUploadResponse(BaseModel):
    file_url: str
    storage_path: str
    file_name: str


class FilesServiceClient:
    """
    Делегирует загрузку файла отдельному сервису (Google Drive / S3).

    Мы передаём file_id из Telegram и минимальные метаданные, после чего
    микросервис возвращает конечный URL и путь для сохранения в заявке.
    """

    def __init__(self, base_url: str, *, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def upload_telegram_file(
        self,
        *,
        telegram_file_id: str,
        file_name: str,
        warehouse: str,
        category: str,
        subcategory: str,
        author_id: int,
    ) -> FileUploadResponse:
        payload: Dict[str, Any] = {
            "telegram_file_id": telegram_file_id,
            "file_name": file_name,
            "warehouse": warehouse,
            "category": category,
            "subcategory": subcategory,
            "author_id": author_id,
        }
        url = f"{self.base_url}/files/from-telegram"
        headers = get_api_headers()

        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return FileUploadResponse.model_validate(response.json())

        return await retry_request(_make_request, max_retries=2)  # Files can be large, fewer retries


