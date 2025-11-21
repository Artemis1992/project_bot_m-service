"""Tests for ApprovalChain and ApprovalStep models."""

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

pytestmark = pytest.mark.django_db

from approvals_app.models import (
    ApprovalChain,
    ApprovalStep,
    ChainStatus,
    StepStatus,
    DEFAULT_APPROVAL_FLOW,
)


@pytest.mark.django_db
class TestApprovalChain:
    def test_create_approval_chain(self):
        """Test creating an approval chain."""
        chain = ApprovalChain.objects.create(
            request_id=1,
            summary="Test request summary",
        )
        assert chain.id is not None
        assert chain.status == ChainStatus.PENDING
        assert chain.current_step_order == 1

    def test_mark_approved_moves_to_next_step(self):
        """Test that approving a step moves to next step."""
        chain = ApprovalChain.objects.create(
            request_id=1,
            summary="Test request",
        )
        step1 = ApprovalStep.objects.create(
            chain=chain,
            order=1,
            approver_name="Approver 1",
            status=StepStatus.WAITING,
        )
        step2 = ApprovalStep.objects.create(
            chain=chain,
            order=2,
            approver_name="Approver 2",
            status=StepStatus.WAITING,
        )

        with patch.object(chain, "_sync_request_status"), \
             patch.object(chain, "_notify_next_approver"):
            chain.mark_approved(step1)

        step1.refresh_from_db()
        chain.refresh_from_db()
        assert step1.status == StepStatus.APPROVED
        assert chain.current_step_order == 2
        assert chain.status == ChainStatus.PENDING

    def test_mark_approved_final_step_approves_chain(self):
        """Test that approving final step approves the chain."""
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
             patch.object(chain, "_notify_author_approved"):
            chain.mark_approved(step)

        step.refresh_from_db()
        chain.refresh_from_db()
        assert step.status == StepStatus.APPROVED
        assert chain.status == ChainStatus.APPROVED

    def test_mark_rejected_rejects_chain(self):
        """Test that rejecting a step rejects the chain."""
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
            chain.mark_rejected(step, comment="Not approved")

        step.refresh_from_db()
        chain.refresh_from_db()
        assert step.status == StepStatus.REJECTED
        assert step.comment == "Not approved"
        assert chain.status == ChainStatus.REJECTED

    def test_sync_request_status_called(self):
        """Test that sync_request_status is called."""
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

        with patch("approvals_app.models.get_requests_client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.update_request_status_sync.return_value = None
            mock_client.return_value = mock_client_instance

            with patch.object(chain, "_notify_author_approved"):
                chain.mark_approved(step)

            # Verify sync was called
            mock_client_instance.update_request_status_sync.assert_called()


@pytest.mark.django_db
class TestApprovalStep:
    def test_create_approval_step(self):
        """Test creating an approval step."""
        chain = ApprovalChain.objects.create(
            request_id=1,
            summary="Test request",
        )
        step = ApprovalStep.objects.create(
            chain=chain,
            order=1,
            approver_name="Test Approver",
            approver_role="Manager",
            telegram_username="@test",
            status=StepStatus.WAITING,
        )
        assert step.id is not None
        assert step.status == StepStatus.WAITING
        assert "Test Approver" in str(step)

