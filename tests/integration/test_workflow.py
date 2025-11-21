"""Integration tests for complete workflow."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock

import pytest

# Setup Django for requests_service
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "requests_service"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_requests.settings")

import django
django.setup()

pytestmark = pytest.mark.django_db

from requests_app.models import Request, RequestStatus

# Import approvals models
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "approvals_service"))
from approvals_app.models import ApprovalChain, ChainStatus


@pytest.mark.django_db
class TestCompleteWorkflow:
    """Test complete request approval workflow."""

    def test_create_request_starts_approval_chain(self):
        """Test that creating a request starts approval chain."""
        with patch("requests_app.approvals_client.get_approvals_client") as mock_approvals, \
             patch("requests_app.reporting_client.get_reporting_client") as mock_reporting:
            
            mock_approvals_instance = Mock()
            mock_approvals_instance.start_approval_chain_sync.return_value = {"id": 1}
            mock_approvals.return_value = mock_approvals_instance
            
            mock_reporting_instance = Mock()
            mock_reporting_instance.report_request_sync.return_value = None
            mock_reporting.return_value = mock_reporting_instance
            
            with patch.dict(os.environ, {
                "APPROVALS_SERVICE_ENABLED": "true",
                "REPORTING_SERVICE_ENABLED": "true",
            }):
                request = Request.objects.create(
                    tg_user_id=12345,
                    warehouse="Алматы",
                    category="Авто",
                    subcategory="Ремонт",
                    amount="10000.00",
                )
                
                # Simulate approval chain start
                from requests_app.approvals_client import get_approvals_client
                client = get_approvals_client()
                client.start_approval_chain_sync(request.id, request.build_summary_text())
                
                # Verify request status updated
                request.refresh_from_db()
                assert request.status == RequestStatus.IN_PROGRESS
                assert request.current_level == 1

    def test_approval_chain_workflow(self):
        """Test complete approval chain workflow."""
        # Create request
        request = Request.objects.create(
            tg_user_id=12345,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт",
            amount="10000.00",
        )
        
        # Create approval chain
        chain = ApprovalChain.objects.create(
            request_id=request.id,
            summary=request.build_summary_text(),
        )
        
        from approvals_app.models import ApprovalStep, StepStatus
        
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
        
        # Approve first step
        with patch.object(chain, "_sync_request_status"), \
             patch.object(chain, "_notify_next_approver"):
            chain.mark_approved(step1)
        
        chain.refresh_from_db()
        assert chain.current_step_order == 2
        assert chain.status == ChainStatus.PENDING
        
        # Approve final step
        with patch.object(chain, "_sync_request_status"), \
             patch.object(chain, "_notify_author_approved"):
            chain.mark_approved(step2)
        
        chain.refresh_from_db()
        assert chain.status == ChainStatus.APPROVED

