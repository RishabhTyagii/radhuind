from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class CycleTyreItem(models.Model):
    """Master list of cycle tyres (BOX TYPE + SIZE + MATERIAL + BRAND)."""
    box_type = models.CharField("BOX TYPE", max_length=30)   # e.g. "6 ply"
    size = models.CharField("SIZE", max_length=50)            # e.g. "28 x 1.5"
    material = models.CharField("MATERIAL", max_length=20)    # e.g. CTC / NYL
    brand = models.CharField("BRAND", max_length=80)

    stock = models.IntegerField("STOCK", default=0)
    rfm_stock = models.IntegerField("R.F.M. Stock", default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["size", "box_type", "material", "brand"]
        unique_together = ("box_type", "size", "material", "brand")

    def __str__(self):
        return f"{self.size} {self.box_type} {self.material} {self.brand}".strip()

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


class CycleTyreEntry(models.Model):
    """Every day-wise transaction: production, sale or manual adjustment."""
    tyre_item = models.ForeignKey(CycleTyreItem, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=15, choices=ENTRY_TYPE_CHOICES)
    bucket = models.CharField(max_length=15, choices=BUCKET_CHOICES, default="stock")
    quantity = models.IntegerField(help_text="Enter positive quantity")
    date = models.DateField()
    bill_number = models.CharField(max_length=50, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="cycletyre_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name_plural = "Cycle tyre entries"

    def __str__(self):
        return f"{self.date} | {self.tyre_item} | {self.get_entry_type_display()} | {self.quantity}"