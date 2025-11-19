from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from django.db import models


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
        step.save(update_fields=["status", "comment", "updated_at"])
        self.status = ChainStatus.REJECTED
        self.save(update_fields=["status", "updated_at"])

    def mark_approved(self, step: "ApprovalStep") -> None:
        step.status = StepStatus.APPROVED
        step.save(update_fields=["status", "updated_at"])

        next_step = (
            self.steps.filter(order__gt=step.order).order_by("order").first()
        )
        if next_step:
            self.current_step_order = next_step.order
            self.save(update_fields=["current_step_order", "updated_at"])
        else:
            self.status = ChainStatus.APPROVED
            self.save(update_fields=["status", "updated_at"])


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

