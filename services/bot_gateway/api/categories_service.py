"""Client responsible for fetching the warehouse/category tree."""

from __future__ import annotations

from typing import Iterable, List

import httpx
from pydantic import BaseModel, Field

from .http_utils import get_api_headers
from .retry_client import retry_request


class Subcategory(BaseModel):
    id: str
    name: str
    requires_comment: bool = Field(default=False, description="Например, для штрафов")
    is_custom_input: bool = Field(
        default=False, description="Если True — пользователь вводит название вручную"
    )


class Category(BaseModel):
    id: str
    name: str
    subcategories: List[Subcategory] = Field(default_factory=list)


class Warehouse(BaseModel):
    id: str
    name: str
    categories: List[Category] = Field(default_factory=list)


class CategoriesServiceClient:
    """
    Загружает структуру расходов из categories_service (Google Sheets источник).

    Ожидаем, что сервис отдаёт дерево вида:
    [
        {
            "id": "almaty",
            "name": "Алматы",
            "categories": [
                {
                    "id": "auto",
                    "name": "Авто",
                    "subcategories": [
                        {"id": "repair", "name": "Ремонт авто"}
                    ]
                }
            ]
        }
    ]
    """

    def __init__(self, base_url: str, *, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def fetch_structure(self) -> List[Warehouse]:
        """
        Возвращает свежую структуру для FSM.
        """
        url = f"{self.base_url}/categories/tree"
        headers = get_api_headers()

        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        payload = await retry_request(_make_request)
        return [Warehouse.model_validate(raw) for raw in payload]

    async def list_warehouses(self) -> List[Warehouse]:
        return await self.fetch_structure()

    @staticmethod
    def find_categories(tree: Iterable[Warehouse], warehouse_id: str) -> List[Category]:
        for warehouse in tree:
            if warehouse.id == warehouse_id:
                return warehouse.categories
        return []

