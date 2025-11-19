from django.test import TestCase
from django.utils.text import slugify

from categories_app.models import Warehouse, Category, Subcategory
from categories_app.sheets_sync import (
    CategoriesSheetSync,
    WAREHOUSE_KEYS,
    CATEGORY_KEYS,
    SUBCATEGORY_KEYS,
    DETAIL_KEYS,
)


class _StubWorksheet:
    def __init__(self, records):
        self.records = records

    def get_all_records(self):
        return self.records


class _StubClient:
    def __init__(self, records):
        self.records = records

    def open_by_key(self, _key):
        return self

    def worksheet(self, _name):
        return _StubWorksheet(self.records)


class CategoriesSheetSyncTests(TestCase):
    def test_sync_creates_entities_from_sheet_rows(self):
        records = [
            {
                WAREHOUSE_KEYS[0]: "Almaty",
                CATEGORY_KEYS[0]: "Auto",
                SUBCATEGORY_KEYS[0]: "Repair",
                DETAIL_KEYS[0]: "Tires",
                "�?�?�?�?��?�'���?���": "�?�+�?�����'��>",
            }
        ]
        sync = CategoriesSheetSync(
            spreadsheet_key="dummy",
            worksheet_name="Categories",
        )
        sync._client = _StubClient(records)  # noqa: SLF001 - подмена gspread клиента

        result = sync.sync()

        self.assertEqual(result["rows_processed"], 1)
        self.assertEqual(Warehouse.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Subcategory.objects.count(), 1)

        subcategory = Subcategory.objects.first()
        self.assertEqual(subcategory.name, "Tires")
        self.assertEqual(subcategory.requires_comment, True)
        self.assertEqual(
            subcategory.slug,
            slugify("Repair-Tires", allow_unicode=True),
        )
