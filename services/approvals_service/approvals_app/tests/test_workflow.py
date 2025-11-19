from rest_framework import status
from rest_framework.test import APITestCase

from approvals_app.models import ApprovalChain, StepStatus


class ApprovalWorkflowTests(APITestCase):
    def setUp(self) -> None:
        self.start_payload = {
            "request_id": 501,
            "summary": "Склад: Алматы\nКатегория: Авто\nСумма: 15000",
        }

    def test_start_chain_creates_steps(self) -> None:
        response = self.client.post(
            "/api/approvals/start/",
            self.start_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chain = ApprovalChain.objects.get(request_id=501)
        self.assertEqual(chain.steps.count(), 4)
        self.assertEqual(chain.current_step_order, 1)

    def test_approve_then_reject(self) -> None:
        chain = self._create_chain()
        approve_response = self.client.post(
            f"/api/approvals/{chain.request_id}/approve/",
            {"actor_username": "denis"},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        chain.refresh_from_db()
        first_step = chain.steps.get(order=1)
        self.assertEqual(first_step.status, StepStatus.APPROVED)
        self.assertEqual(chain.current_step_order, 2)

        reject_response = self.client.post(
            f"/api/approvals/{chain.request_id}/reject/",
            {"actor_username": "jasulan", "comment": "Нужны детали"},
            format="json",
        )
        self.assertEqual(reject_response.status_code, status.HTTP_200_OK)
        chain.refresh_from_db()
        second_step = chain.steps.get(order=2)
        self.assertEqual(second_step.status, StepStatus.REJECTED)
        self.assertEqual(chain.status, "rejected")

    def _create_chain(self) -> ApprovalChain:
        response = self.client.post(
            "/api/approvals/start/",
            self.start_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return ApprovalChain.objects.get(request_id=self.start_payload["request_id"])


