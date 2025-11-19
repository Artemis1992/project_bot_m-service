from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from requests_app.models import Request


class RequestAPITests(APITestCase):
    def setUp(self) -> None:
        self.base_payload = {
            "tg_user_id": 1001,
            "author_username": "test_user",
            "author_full_name": "Test User",
            "warehouse": "Алматы",
            "category": "Авто",
            "subcategory": "Ремонт авто",
            "amount": "12000.00",
            "comment": "Плановое обслуживание",
        }

    def test_create_request_success(self) -> None:
        response = self.client.post("/api/requests/", self.base_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["warehouse"], "Алматы")

    def test_create_request_with_invalid_amount(self) -> None:
        payload = {**self.base_payload, "amount": "-1"}
        response = self.client.post("/api/requests/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_partial_update_allowed_while_new(self) -> None:
        request_obj = Request.objects.create(
            tg_user_id=1001,
            author_username="user",
            author_full_name="User",
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="1000.00",
            comment="",
        )
        response = self.client.patch(
            f"/api/requests/{request_obj.id}/",
            {"amount": "1500.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(str(request_obj.amount), "1500.00")

    def test_attach_file_to_request(self) -> None:
        request_obj = Request.objects.create(
            tg_user_id=1001,
            author_username="user",
            author_full_name="User",
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="1000.00",
            comment="",
        )
        payload = {
            "file_url": "https://files.local/path/file.pdf",
            "storage_path": "/Авто/Ремонт/2024-01/file.pdf",
            "file_name": "file.pdf",
        }
        response = self.client.post(
            f"/api/requests/{request_obj.id}/attach/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("attachment_id", response.data)


