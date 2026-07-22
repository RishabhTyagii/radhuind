from django.db import models

MODULE_CHOICES = [
    ("tyre", "Auto Tyre"),
    ("tube", "Cycle Tube"),
    ("cycletyre", "Cycle Tyre"),
]


class TallyItemMapping(models.Model):
    """Maps a Tally stock-item name to one of our items in the 3 modules."""
    tally_item_name = models.CharField(max_length=150, unique=True)
    module = models.CharField(max_length=15, choices=MODULE_CHOICES)
    item_id = models.PositiveIntegerField(help_text="The ID of the matching item in that module")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tally_item_name"]

    def __str__(self):
        return f"{self.tally_item_name} → {self.get_module_display()} #{self.item_id}"

    def get_item(self):
        if self.module == "tyre":
            from stock.models import TyreItem
            return TyreItem.objects.filter(pk=self.item_id).first()
        elif self.module == "tube":
            from cycletube.models import CycleTubeItem
            return CycleTubeItem.objects.filter(pk=self.item_id).first()
        elif self.module == "cycletyre":
            from cycletyres.models import CycleTyreItem
            return CycleTyreItem.objects.filter(pk=self.item_id).first()
        return None


class TallyInvoice(models.Model):
    """One synced Sales voucher from Tally, with GST breakup."""
    voucher_number = models.CharField(max_length=50, unique=True)
    voucher_date = models.DateField()
    party_name = models.CharField(max_length=200, blank=True)
    taxable_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_synced = models.BooleanField(default=False, help_text="True if all line items matched & stock was reduced")
    raw_payload = models.TextField(blank=True)
    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-voucher_date", "-synced_at"]

    def __str__(self):
        return f"{self.voucher_number} | {self.voucher_date} | {self.party_name} | ₹{self.total_value}"

    @property
    def gst_total(self):
        return self.cgst + self.sgst + self.igst


LOG_LEVEL_CHOICES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("error", "Error"),
]


class TallySyncLog(models.Model):
    invoice = models.ForeignKey(TallyInvoice, on_delete=models.CASCADE, null=True, blank=True, related_name="logs")
    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, default="info")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.level}] {self.message[:80]}"