from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import gspread
from django.db import transaction
from django.utils.text import slugify

from .models import Warehouse, Category, Subcategory


WAREHOUSE_KEYS = ("Выберите склад", "Склад")
CATEGORY_KEYS = ("Категория",)
SUBCATEGORY_KEYS = ("Выберите Категорию", "Подкатегория")
DETAIL_KEYS = ("Выберите подкатегорию",)


@dataclass
class NormalisedRow:
    warehouse: str
    category: str
    canonical_subcategory: str
    detail_option: Optional[str]
    display_name: str
    requires_comment: bool
    is_custom_input: bool


class CategoriesSheetSync:
    """
    Loads List2 ("Категории расходов") and projects it into the local DB.
    """

    def __init__(
        self,
        spreadsheet_key: str,
        worksheet_name: str,
        *,
        service_account_file: str | None = None,
        service_account_json: str | None = None,
    ) -> None:
        self.spreadsheet_key = spreadsheet_key
        self.worksheet_name = worksheet_name
        self.service_account_file = service_account_file
        self.service_account_json = service_account_json
        self._client: gspread.Client | None = None

    def _build_client(self) -> gspread.Client:
        if self._client:
            return self._client
        if self.service_account_file:
            self._client = gspread.service_account(filename=self.service_account_file)
        elif self.service_account_json:
            self._client = gspread.service_account_from_dict(
                json.loads(self.service_account_json)
            )
        else:
            self._client = gspread.service_account()
        return self._client

    def fetch_rows(self) -> List[Dict[str, Any]]:
        worksheet = (
            self._build_client()
            .open_by_key(self.spreadsheet_key)
            .worksheet(self.worksheet_name)
        )
        return worksheet.get_all_records()

    def _first_value(self, row: Dict[str, Any], keys: Iterable[str]) -> str | None:
        for key in keys:
            value = row.get(key)
            if isinstance(value, str):
                value = value.strip()
            if value and value != "-":
                return str(value).strip()
        return None

    def _normalise_row(self, row: Dict[str, Any]) -> NormalisedRow | None:
        warehouse = self._first_value(row, WAREHOUSE_KEYS)
        category = self._first_value(row, CATEGORY_KEYS)
        subcategory = self._first_value(row, SUBCATEGORY_KEYS)
        if not (warehouse and category and subcategory):
            return None

        detail_option = self._first_value(row, DETAIL_KEYS)
        name = (detail_option or subcategory).strip()
        comment_hint = (row.get("Комментарий") or "").lower()
        requires_comment = "обязател" in comment_hint
        is_custom_input = "другое" in name.lower()

        return NormalisedRow(
            warehouse=warehouse,
            category=category,
            canonical_subcategory=subcategory,
            detail_option=detail_option,
            display_name=name,
            requires_comment=requires_comment,
            is_custom_input=is_custom_input,
        )

    @transaction.atomic
    def sync(self) -> Dict[str, int]:
        rows = [
            normalised
            for normalised in (self._normalise_row(row) for row in self.fetch_rows())
            if normalised
        ]

        processed = 0
        for row in rows:
            warehouse, _ = Warehouse.objects.get_or_create(
                slug=slugify(row.warehouse, allow_unicode=True),
                defaults={"name": row.warehouse},
            )
            category, _ = Category.objects.get_or_create(
                warehouse=warehouse,
                slug=slugify(row.category, allow_unicode=True),
                defaults={"name": row.category},
            )
            subcategory_slug_source = f"{row.canonical_subcategory}-{row.detail_option or ''}"
            subcategory, _ = Subcategory.objects.update_or_create(
                category=category,
                slug=slugify(subcategory_slug_source, allow_unicode=True),
                defaults={
                    "name": row.display_name,
                    "requires_comment": row.requires_comment,
                    "is_custom_input": row.is_custom_input,
                },
            )
            processed += 1

        return {
            "rows_processed": processed,
            "warehouses": Warehouse.objects.count(),
            "categories": Category.objects.count(),
            "subcategories": Subcategory.objects.count(),
        }

