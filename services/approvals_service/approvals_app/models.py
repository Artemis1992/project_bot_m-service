from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from django.db import models
from django.utils import timezone


class ChainStatus(models.TextChoices):
    PENDING = "pending", "В работе"
    APPROVED = "approved", "Утверждена"
    REJECTED = "rejected", "Отклонена"


class StepStatus(models.TextChoices):
    WAITING = "waiting", "Ожидает"
    APPROVED = "approved", "Утверждено"
    REJECTED = "rejected", "Отклонено"
    SKIPPED = "skipped", "Пропущено"


@dataclass(frozen=True)
class Approver:
    order: int
    name: str
    role: str
    telegram_username: str | None = None


DEFAULT_APPROVAL_FLOW: List[Approver] = [
    Approver(1, "Денис", "Коммерческий директор"),
    Approver(2, "Жасулан", "Исполнительный директор"),
    Approver(3, "Мейржан", "Финансовый директор"),
    Approver(4, "Лязат/Айгуль", "Оплата"),
]


class ApprovalChain(models.Model):
    request_id = models.PositiveIntegerField(unique=True)
    summary = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=ChainStatus.choices,
        default=ChainStatus.PENDING,
    )
    current_step_order = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Согласование заявки {self.request_id}"

    def mark_rejected(self, step: "ApprovalStep", comment: str | None = None) -> None:
        step.status = StepStatus.REJECTED
        if comment:
            step.comment = comment
        step.acted_at = timezone.now()
        step.save(update_fields=["status", "comment", "acted_at", "updated_at"])
        self.status = ChainStatus.REJECTED
        self.save(update_fields=["status", "updated_at"])
        
        # Синхронизируем статус с requests_service
        self._sync_request_status("rejected", step.order)
        # Уведомляем автора об отклонении
        self._notify_author_rejected(comment)

    def mark_approved(self, step: "ApprovalStep") -> None:
        step.status = StepStatus.APPROVED
        step.acted_at = timezone.now()
        step.save(update_fields=["status", "acted_at", "updated_at"])

        next_step = (
            self.steps.filter(order__gt=step.order).order_by("order").first()
        )
        if next_step:
            self.current_step_order = next_step.order
            self.save(update_fields=["current_step_order", "updated_at"])
            # Синхронизируем статус - все еще в процессе
            self._sync_request_status("in_progress", next_step.order)
            # Уведомляем следующего согласующего
            self._notify_next_approver(next_step)
        else:
            self.status = ChainStatus.APPROVED
            self.save(update_fields=["status", "updated_at"])
            # Синхронизируем статус - утверждена
            self._sync_request_status("approved", step.order)
            # Уведомляем автора об утверждении
            self._notify_author_approved()

    def _sync_request_status(self, status: str, current_level: int) -> None:
        """Sync request status with requests_service."""
        try:
            from .requests_client import get_requests_client
            client = get_requests_client()
            client.update_request_status_sync(self.request_id, status, current_level)
        except Exception:
            # Логируем, но не падаем если синхронизация не удалась
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to sync request {self.request_id} status to requests_service")

    def _notify_next_approver(self, step: "ApprovalStep") -> None:
        """Notify next approver (via webhook or queue)."""
        try:
            from .notifications_client import get_notifications_client
            client = get_notifications_client()
            client.notify_approver_async(
                telegram_username=step.telegram_username,
                request_id=self.request_id,
                summary=self.summary,
                step_order=step.order,
                approver_name=step.approver_name,
            )
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to notify approver for request {self.request_id}")

    def _notify_author_approved(self) -> None:
        """Notify author that request was approved."""
        try:
            from .notifications_client import get_notifications_client
            client = get_notifications_client()
            # Get author ID from requests_service
            client.notify_author_approved_async(self.request_id)
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to notify author for request {self.request_id}")

    def _notify_author_rejected(self, comment: str | None = None) -> None:
        """Notify author that request was rejected."""
        try:
            from .notifications_client import get_notifications_client
            client = get_notifications_client()
            client.notify_author_rejected_async(self.request_id, comment)
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to notify author for request {self.request_id}")


class ApprovalStep(models.Model):
    chain = models.ForeignKey(
        ApprovalChain,
        related_name="steps",
        on_delete=models.CASCADE,
    )
    order = models.PositiveSmallIntegerField()
    approver_name = models.CharField(max_length=100)
    approver_role = models.CharField(max_length=150, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StepStatus.choices,
        default=StepStatus.WAITING,
    )
    comment = models.TextField(blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order",)

    def __str__(self) -> str:
        return f"{self.approver_name}: {self.get_status_display()}"

