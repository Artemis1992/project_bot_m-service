from rest_framework import status
from rest_framework.test import APITestCase

from categories_app.models import Warehouse, Category, Subcategory


class CategoryAPITests(APITestCase):
    def setUp(self) -> None:
        almaty = Warehouse.objects.create(slug="almaty", name="Алматы")
        auto = Category.objects.create(warehouse=almaty, slug="auto", name="Авто")
        Subcategory.objects.create(
            category=auto,
            slug="repair",
            name="Ремонт авто",
            requires_comment=False,
        )

    def test_tree_endpoint_returns_nested_structure(self) -> None:
        response = self.client.get("/api/categories/tree")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "Алматы")
        self.assertEqual(payload[0]["categories"][0]["subcategories"][0]["name"], "Ремонт авто")

    def test_sync_endpoint_placeholder(self) -> None:
        response = self.client.post("/api/categories/sync")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("detail", response.json())


