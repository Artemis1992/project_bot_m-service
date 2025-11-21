"""Tests for approvals_service API endpoints."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "approvals_service"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "approvals_service.settings")

import django
django.setup()

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db

from approvals_app.models import ApprovalChain, ApprovalStep, ChainStatus, StepStatus


class ApprovalAPITests(APITestCase):
    """Tests for approval API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.api_key = "test-api-key"
        os.environ["SERVICE_API_KEY"] = self.api_key

    def _authenticated_request(self, method, url, **kwargs):
        """Make authenticated request."""
        kwargs.setdefault("HTTP_X_API_KEY", self.api_key)
        return getattr(self.client, method.lower())(url, **kwargs)

    def test_start_approval_flow(self):
        """Test starting an approval flow."""
        payload = {
            "request_id": 1,
            "summary": "Test request summary",
        }
        response = self._authenticated_request(
            "post",
            "/api/approvals/start/",
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["request_id"], 1)
        self.assertEqual(len(response.data["steps"]), 4)  # DEFAULT_APPROVAL_FLOW has 4 steps

    def test_start_approval_flow_without_auth_fails(self):
        """Test that starting flow without API key fails."""
        payload = {
            "request_id": 1,
            "summary": "Test request summary",
        }
        response = self.client.post("/api/approvals/start/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_approve_step(self):
        """Test approving a step."""
        chain = ApprovalChain.objects.create(
            request_id=1,
            summary="Test request",
        )
        step = ApprovalStep.objects.create(
            chain=chain,
            order=1,
            approver_name="Approver 1",
            status=StepStatus.WAITING,
        )

        with patch.object(chain, "_sync_request_status"), \
             patch.object(chain, "_notify_next_approver"):
            payload = {
                "actor_username": "approver1",
                "comment": "",
            }
            response = self._authenticated_request(
                "post",
                f"/api/approvals/{chain.request_id}/approve/",
                data=payload,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_step(self):
        """Test rejecting a step."""
        chain = ApprovalChain.objects.create(
            request_id=1,
            summary="Test request",
        )
        step = ApprovalStep.objects.create(
            chain=chain,
            order=1,
            approver_name="Approver 1",
            status=StepStatus.WAITING,
        )

        with patch.object(chain, "_sync_request_status"), \
             patch.object(chain, "_notify_author_rejected"):
            payload = {
                "actor_username": "approver1",
                "comment": "Not approved",
            }
            response = self._authenticated_request(
                "post",
                f"/api/approvals/{chain.request_id}/reject/",
                data=payload,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            chain.refresh_from_db()
            self.assertEqual(chain.status, ChainStatus.REJECTED)

    def test_retrieve_approval_chain(self):
        """Test retrieving an approval chain."""
        chain = ApprovalChain.objects.create(
            request_id=1,
            summary="Test request",
        )
        ApprovalStep.objects.create(
            chain=chain,
            order=1,
            approver_name="Approver 1",
        )

        response = self._authenticated_request(
            "get",
            f"/api/approvals/{chain.request_id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["request_id"], 1)
        self.assertEqual(len(response.data["steps"]), 1)

