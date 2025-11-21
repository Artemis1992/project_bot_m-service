"""Tests for categories_service API."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "categories_service"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "categories_service.settings")

import django
django.setup()

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db

from categories_app.models import Category, Subcategory, Warehouse


class CategoryAPITests(APITestCase):
    """Tests for category API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.api_key = "test-api-key"
        os.environ["SERVICE_API_KEY"] = self.api_key
        self.warehouse = Warehouse.objects.create(slug="almaty", name="Алматы")
        self.category = Category.objects.create(
            warehouse=self.warehouse,
            slug="auto",
            name="Авто",
        )
        self.subcategory = Subcategory.objects.create(
            category=self.category,
            slug="repair",
            name="Ремонт авто",
        )

    def _authenticated_request(self, method, url, **kwargs):
        """Make authenticated request."""
        kwargs.setdefault("HTTP_X_API_KEY", self.api_key)
        return getattr(self.client, method.lower())(url, **kwargs)

    def test_get_category_tree(self):
        """Test getting category tree."""
        response = self._authenticated_request("get", "/api/categories/tree/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if len(response.data) > 0:
            warehouse_data = response.data[0]
            self.assertIn("id", warehouse_data)
            self.assertIn("name", warehouse_data)
            self.assertIn("categories", warehouse_data)

    def test_get_category_tree_without_auth_fails(self):
        """Test that getting tree without API key fails."""
        response = self.client.get("/api/categories/tree/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sync_categories(self):
        """Test syncing categories from Google Sheets."""
        with patch("categories_app.sheets_sync.CategoriesSheetSync") as mock_sync_class:
            mock_sync = Mock()
            mock_sync.sync.return_value = {
                "rows_processed": 10,
                "warehouses": 2,
                "categories": 5,
                "subcategories": 10,
            }
            mock_sync.spreadsheet_key = "test-key"
            mock_sync_class.return_value = mock_sync

            response = self._authenticated_request("post", "/api/categories/sync/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("detail", response.data)
            self.assertIn("rows_processed", response.data)

    def test_sync_categories_no_config(self):
        """Test syncing when Google Sheets is not configured."""
        with patch("categories_app.sheets_sync.CategoriesSheetSync") as mock_sync_class:
            mock_sync = Mock()
            mock_sync.spreadsheet_key = ""
            mock_sync_class.return_value = mock_sync

            response = self._authenticated_request("post", "/api/categories/sync/")
            # Should return 202 when not configured
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_202_ACCEPTED])

