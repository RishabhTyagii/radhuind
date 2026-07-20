from django.db import models
from django.contrib.auth.models import User


class TyreItem(models.Model):
    """Master list of tyres (TYR + PATTERN + TYPE)."""
    tyre = models.CharField("TYRE", max_length=50)
    pattern = models.CharField("PATTERN", max_length=80)
    type = models.CharField("TYPE", max_length=20)  # TT / TL
    
    # Current running balances (buckets)
    repair_tyre_stock = models.IntegerField("Repair Tyre Stock", default=0)
    rfm_ok_tyre = models.IntegerField("RFM OK Tyre", default=0)
    old_tyres_2025 = models.IntegerField("2025 Old Tyres", default=0)
    stock = models.IntegerField("STOCK", default=0)
    on_hold_export = models.IntegerField("On hold for Export / OR", default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tyre", "pattern", "type"]
        unique_together = ("tyre", "pattern", "type")

    def __str__(self):
        return f"{self.tyre} {self.pattern} {self.type}"

    @property
    def total_stock(self):
        return (
            self.repair_tyre_stock
            + self.rfm_ok_tyre
            + self.old_tyres_2025
            + self.stock
            + self.on_hold_export
        )


BUCKET_CHOICES = [
    ("stock", "STOCK"),
    ("repair_tyre_stock", "Repair Tyre Stock"),
    ("rfm_ok_tyre", "RFM OK Tyre"),
    ("old_tyres_2025", "2025 Old Tyres"),
    ("on_hold_export", "On hold for Export / OR"),
]

ENTRY_TYPE_CHOICES = [
    ("production", "Production (Daily Curing)"),
    ("dispatch", "Dispatch"),
    ("adjustment", "Stock Adjustment"),
]


class DailyEntry(models.Model):
    """Every day-wise transaction: production, dispatch or manual adjustment."""
    tyre_item = models.ForeignKey(TyreItem, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=15, choices=ENTRY_TYPE_CHOICES)
    bucket = models.CharField(max_length=25, choices=BUCKET_CHOICES, default="stock")
    quantity = models.IntegerField(help_text="Enter positive quantity")
    date = models.DateField()
    bill_number = models.CharField(max_length=50, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="stock_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} | {self.tyre_item} | {self.get_entry_type_display()} | {self.quantity}"
