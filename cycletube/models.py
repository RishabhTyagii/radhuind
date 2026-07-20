from django.db import models
from django.contrib.auth.models import User


class CycleTubeItem(models.Model):
    """Master list of cycle tubes (SIZE + TYPE + BRAND)."""
    size = models.CharField("SIZE", max_length=50)
    type = models.CharField("TYPE", max_length=20)     # e.g. JT / MLD
    brand = models.CharField("BRAND", max_length=80)

    stock = models.IntegerField("STOCK", default=0)
    rfm_stock = models.IntegerField("R.F.M. Stock", default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["size", "type", "brand"]
        unique_together = ("size", "type", "brand")

    def __str__(self):
        return f"{self.size} {self.type} {self.brand}".strip()

    @property
    def total_stock(self):
        return self.stock + self.rfm_stock


BUCKET_CHOICES = [
    ("stock", "STOCK"),
    ("rfm_stock", "R.F.M. Stock"),
]

ENTRY_TYPE_CHOICES = [
    ("production", "Production"),
    ("sale", "Sale / Dispatch"),
    ("adjustment", "Stock Adjustment"),
]


class CycleTubeEntry(models.Model):
    """Every day-wise transaction: production, sale or manual adjustment."""
    tube_item = models.ForeignKey(CycleTubeItem, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=15, choices=ENTRY_TYPE_CHOICES)
    bucket = models.CharField(max_length=15, choices=BUCKET_CHOICES, default="stock")
    quantity = models.IntegerField(help_text="Enter positive quantity")
    date = models.DateField()
    bill_number = models.CharField(max_length=50, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="cycletube_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name_plural = "Cycle tube entries"

    def __str__(self):
        return f"{self.date} | {self.tube_item} | {self.get_entry_type_display()} | {self.quantity}"