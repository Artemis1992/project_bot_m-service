"""Django signals for request model."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Request
from .reporting_client import get_reporting_client

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Request)
def update_reporting_service(sender, instance: Request, created: bool, **kwargs):
    """
    Automatically update reporting_service when request is created or updated.
    """
    try:
        reporting_client = get_reporting_client()
        reporting_client.report_request_sync(instance)
    except Exception as exc:
        logger.error(f"Failed to sync request {instance.id} to reporting_service: {exc}")






