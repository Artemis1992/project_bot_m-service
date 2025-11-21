"""Extended API tests for requests_service with authentication."""

import os
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db

from requests_app.choices import RequestStatus
from requests_app.models import Attachment, Request


class RequestAPIExtendedTests(APITestCase):
    """Extended API tests with authentication."""

    def setUp(self):
        """Set up test data."""
        self.api_key = "test-api-key"
        os.environ["SERVICE_API_KEY"] = self.api_key
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

    def _authenticated_request(self, method, url, **kwargs):
        """Make authenticated request."""
        kwargs.setdefault("HTTP_X_API_KEY", self.api_key)
        return getattr(self.client, method.lower())(url, **kwargs)

    def test_create_request_without_auth_fails(self):
        """Test that creating request without API key fails."""
        response = self.client.post("/api/requests/", self.base_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_request_with_auth_succeeds(self):
        """Test that creating request with valid API key succeeds."""
        response = self._authenticated_request("post", "/api/requests/", data=self.base_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_request_triggers_approval_chain(self):
        """Test that creating request triggers approval chain."""
        with patch("requests_app.approvals_client.get_approvals_client") as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.start_approval_chain_sync.return_value = {"id": 1}
            
            with patch.dict(os.environ, {"APPROVALS_SERVICE_ENABLED": "true"}):
                response = self._authenticated_request("post", "/api/requests/", data=self.base_payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                # Check that approval chain was started
                request_obj = Request.objects.get(id=response.data["id"])
                self.assertEqual(request_obj.status, RequestStatus.IN_PROGRESS)
                self.assertEqual(request_obj.current_level, 1)

    def test_create_request_triggers_reporting(self):
        """Test that creating request triggers reporting."""
        with patch("requests_app.reporting_client.get_reporting_client") as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.report_request_sync.return_value = {"google_row_id": "A1"}
            
            with patch.dict(os.environ, {"REPORTING_SERVICE_ENABLED": "true"}):
                response = self._authenticated_request("post", "/api/requests/", data=self.base_payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                # Verify reporting was called
                mock_client_instance.report_request_sync.assert_called_once()

    def test_update_request_updates_reporting(self):
        """Test that updating request updates reporting."""
        request_obj = Request.objects.create(
            tg_user_id=1001,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="1000.00",
        )
        
        with patch("requests_app.reporting_client.get_reporting_client") as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.report_request_sync.return_value = None
            
            with patch.dict(os.environ, {"REPORTING_SERVICE_ENABLED": "true"}):
                response = self._authenticated_request(
                    "patch",
                    f"/api/requests/{request_obj.id}/",
                    data={"amount": "1500.00"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Verify reporting was called
                mock_client_instance.report_request_sync.assert_called_once()

    def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require authentication."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.json())

    def test_readiness_endpoint_no_auth_required(self):
        """Test that readiness endpoint doesn't require authentication."""
        response = self.client.get("/ready/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.json())

