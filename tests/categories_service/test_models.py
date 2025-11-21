"""Tests for categories_service models."""

import os
import sys
from pathlib import Path

import pytest

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "categories_service"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "categories_service.settings")

import django
django.setup()

pytestmark = pytest.mark.django_db

from categories_app.models import Category, Subcategory, Warehouse


@pytest.mark.django_db
class TestWarehouse:
    def test_create_warehouse(self):
        """Test creating a warehouse."""
        warehouse = Warehouse.objects.create(
            slug="almaty",
            name="Алматы",
        )
        assert warehouse.id is not None
        assert str(warehouse) == "Алматы"

    def test_warehouse_ordering(self):
        """Test warehouse ordering."""
        Warehouse.objects.create(slug="b", name="Б")
        Warehouse.objects.create(slug="a", name="А")
        warehouses = list(Warehouse.objects.all())
        assert warehouses[0].name == "А"
        assert warehouses[1].name == "Б"


@pytest.mark.django_db
class TestCategory:
    def test_create_category(self):
        """Test creating a category."""
        warehouse = Warehouse.objects.create(slug="almaty", name="Алматы")
        category = Category.objects.create(
            warehouse=warehouse,
            slug="auto",
            name="Авто",
        )
        assert category.id is not None
        assert "Алматы" in str(category)
        assert "Авто" in str(category)

    def test_category_unique_per_warehouse(self):
        """Test that category slug is unique per warehouse."""
        warehouse = Warehouse.objects.create(slug="almaty", name="Алматы")
        Category.objects.create(warehouse=warehouse, slug="auto", name="Авто")
        
        # Try to create duplicate
        with pytest.raises(Exception):  # IntegrityError
            Category.objects.create(warehouse=warehouse, slug="auto", name="Авто2")


@pytest.mark.django_db
class TestSubcategory:
    def test_create_subcategory(self):
        """Test creating a subcategory."""
        warehouse = Warehouse.objects.create(slug="almaty", name="Алматы")
        category = Category.objects.create(
            warehouse=warehouse,
            slug="auto",
            name="Авто",
        )
        subcategory = Subcategory.objects.create(
            category=category,
            slug="repair",
            name="Ремонт авто",
            requires_comment=False,
            is_custom_input=False,
        )
        assert subcategory.id is not None
        assert "Авто" in str(subcategory)
        assert "Ремонт авто" in str(subcategory)

    def test_subcategory_with_required_comment(self):
        """Test subcategory with required comment."""
        warehouse = Warehouse.objects.create(slug="almaty", name="Алматы")
        category = Category.objects.create(
            warehouse=warehouse,
            slug="auto",
            name="Авто",
        )
        subcategory = Subcategory.objects.create(
            category=category,
            slug="fine",
            name="Штраф",
            requires_comment=True,
        )
        assert subcategory.requires_comment is True

