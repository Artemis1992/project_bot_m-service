from __future__ import annotations

from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Warehouse(TimestampedModel):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Category(TimestampedModel):
    warehouse = models.ForeignKey(
        Warehouse,
        related_name="categories",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField()
    name = models.CharField(max_length=150)

    class Meta:
        unique_together = ("warehouse", "slug")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.warehouse.name}: {self.name}"


class Subcategory(TimestampedModel):
    category = models.ForeignKey(
        Category,
        related_name="subcategories",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField()
    name = models.CharField(max_length=150)
    requires_comment = models.BooleanField(default=False)
    is_custom_input = models.BooleanField(default=False)

    class Meta:
        unique_together = ("category", "slug")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.category.name}: {self.name}"

