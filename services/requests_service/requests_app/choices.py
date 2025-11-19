"""Centralized enums/choices used across the service."""

from django.db import models


class RequestStatus(models.TextChoices):
    NEW = "new", "Новая"
    IN_PROGRESS = "in_progress", "На согласовании"
    APPROVED = "approved", "Утверждена"
    REJECTED = "rejected", "Отклонена"
    PAID = "paid", "Оплачена"

