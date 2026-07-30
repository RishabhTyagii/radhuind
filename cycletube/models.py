from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


TUBE_QUALITY_CHOICES = [
    ("normal", "Normal"),
    ("molded", "Molded"),
    ("second", "Second"),
]


class CycleTubeItem(models.Model):
    """Master list of cycle tubes (SIZE + TYPE + BRAND)."""
    size = models.CharField("SIZE", max_length=50)
    type = models.CharField("TYPE", max_length=20)     # e.g. JT / MLD
    brand = models.CharField("BRAND", max_length=80)

    weight = models.DecimalField(
        "Weight (Kg)", max_digits=8, decimal_places=4, default=Decimal("0.0000"),
        help_text="Ek tube ka weight kg mein (e.g. 0.2809)"
    )

    stock = models.IntegerField("STOCK", default=0)
    rfm_stock = models.IntegerField("R.F.M. Stock", default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["size", "type", "brand"]
        unique_together = ("size", "type", "brand")

    def __str__(self):
        w_str = f" [{self.weight}kg]" if self.weight else ""
        return f"{self.size} {self.type} {self.brand}{w_str}".strip()

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

    # Tube quality for production entries (for future filter use)
    tube_quality = models.CharField(
        "Tube Quality", max_length=10,
        choices=TUBE_QUALITY_CHOICES, default="normal",
        help_text="Normal / Molded / Second"
    )

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


# =====================================================================
# Tube constants (same as Excel sheet)
# =====================================================================
PACK_FACTOR = Decimal("0.0075")     # Packing deduction factor
VB_FACTOR   = Decimal("0.015")      # Valve-body deduction factor (less VB)
COMB_FACTOR = Decimal("0.0225")     # Combined factor (-Pck+VB) = 0.0075+0.015


class CycleTubeDailyManualEntry(models.Model):
    """
    Daily manual ground-truth entries for Cycle Tube Production Summary.
    Auto-calculated columns are derived in the view from these + production entries.
    """
    date = models.DateField(unique=True)

    # ---- Manual entry columns ----
    valve_body_issued = models.DecimalField(
        "Valve Body Issued", max_digits=10, decimal_places=2, default=0
    )
    actual_wt_gross = models.DecimalField(
        "Actual wt kgs (Gross)", max_digits=10, decimal_places=2, default=0
    )
    actual_mixing_compound = models.DecimalField(
        "Actual Mixing Compound", max_digits=10, decimal_places=2, default=0
    )
    jali = models.DecimalField(
        "Jali (Wastage)", max_digits=10, decimal_places=2, default=0
    )
    die_wastage = models.DecimalField(
        "Die Wastage", max_digits=10, decimal_places=2, default=0
    )
    tube_cutting = models.DecimalField(
        "Tube Cutting", max_digits=10, decimal_places=2, default=0
    )
    total_tube_waste = models.DecimalField(
        "Total Tube Waste", max_digits=10, decimal_places=2, default=0
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Cycle Tube Daily Manual Entry"
        verbose_name_plural = "Cycle Tube Daily Manual Entries"

    def __str__(self):
        return f"Cycle Tube Daily Manual - {self.date}"