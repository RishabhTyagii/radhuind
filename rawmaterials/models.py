from django.db import models
from django.contrib.auth.models import User


class MaterialGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Material(models.Model):
    group = models.ForeignKey(
        MaterialGroup,
        on_delete=models.CASCADE,
        related_name="materials"
    )

    name = models.CharField(max_length=150)

    unit = models.CharField(
        max_length=20,
        default="Kg"
    )

    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    class Meta:
        ordering = ["group", "name"]

    def __str__(self):
        return self.name


class StockEntry(models.Model):

    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    date = models.DateField()

    opening = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    received_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    received_by = models.CharField(
        max_length=150,
        blank=True
    )

    used_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    closing = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        unique_together = ("material", "date")

    def __str__(self):
        return f"{self.material} - {self.date}"