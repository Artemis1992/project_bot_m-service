"""Tests for Request and Attachment models."""

import pytest
pytestmark = pytest.mark.django_db

from requests_app.choices import RequestStatus
from requests_app.models import Attachment, Request


@pytest.mark.django_db
class TestRequestModel:
    def test_create_request(self):
        """Test creating a request."""
        request = Request.objects.create(
            tg_user_id=12345,
            author_username="test_user",
            author_full_name="Test User",
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="10000.00",
            comment="Test comment",
        )
        assert request.id is not None
        assert request.status == RequestStatus.NEW
        assert request.current_level == 0
        assert request.is_editable_by_author is True

    def test_is_editable_by_author(self):
        """Test is_editable_by_author property."""
        request = Request.objects.create(
            tg_user_id=12345,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="10000.00",
        )
        assert request.is_editable_by_author is True

        request.status = RequestStatus.IN_PROGRESS
        request.save()
        assert request.is_editable_by_author is False

    def test_build_summary_text(self):
        """Test build_summary_text method."""
        request = Request.objects.create(
            tg_user_id=12345,
            author_full_name="Test User",
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            subsubcategory="Газели",
            goal="Плановое обслуживание",
            item_name="Масло",
            quantity="5 л",
            amount="10000.00",
            comment="Срочно",
        )
        summary = request.build_summary_text()
        assert "Служебка" in summary
        assert "Алматы" in summary
        assert "Авто" in summary
        assert "Ремонт авто" in summary
        assert "10000.00" in summary
        assert "Срочно" in summary

    def test_request_str(self):
        """Test Request __str__ method."""
        request = Request.objects.create(
            tg_user_id=12345,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="10000.00",
        )
        assert "Request #" in str(request)
        assert "Алматы" in str(request)


@pytest.mark.django_db
class TestAttachmentModel:
    def test_create_attachment(self):
        """Test creating an attachment."""
        request = Request.objects.create(
            tg_user_id=12345,
            warehouse="Алматы",
            category="Авто",
            subcategory="Ремонт авто",
            amount="10000.00",
        )
        attachment = Attachment.objects.create(
            request=request,
            file_url="https://drive.google.com/file.pdf",
            storage_path="/Авто/Ремонт/2024-01/file.pdf",
            file_name="file.pdf",
        )
        assert attachment.id is not None
        assert attachment.request == request
        assert "file.pdf" in str(attachment)

