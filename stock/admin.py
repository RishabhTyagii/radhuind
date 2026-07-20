from django.contrib import admin
from .models import TyreItem, DailyEntry


@admin.register(TyreItem)
class TyreItemAdmin(admin.ModelAdmin):
    list_display = ("tyre", "pattern", "type", "stock", "repair_tyre_stock", "rfm_ok_tyre", "old_tyres_2025", "on_hold_export", "total_stock", "is_active")
    search_fields = ("tyre", "pattern", "type")
    list_filter = ("type", "is_active")


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "tyre_item", "entry_type", "bucket", "quantity", "user", "remark")
    list_filter = ("entry_type", "bucket", "date")
    search_fields = ("tyre_item__tyre", "remark")
