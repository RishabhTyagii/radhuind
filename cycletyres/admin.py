from django.contrib import admin
from .models import CycleTyreItem, CycleTyreEntry


@admin.register(CycleTyreItem)
class CycleTyreItemAdmin(admin.ModelAdmin):
    list_display = ("size", "box_type", "material", "brand", "stock", "rfm_stock", "total_stock", "is_active")
    search_fields = ("size", "box_type", "material", "brand")
    list_filter = ("material", "is_active")


@admin.register(CycleTyreEntry)
class CycleTyreEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "tyre_item", "entry_type", "bucket", "quantity", "bill_number", "user", "remark")
    list_filter = ("entry_type", "bucket", "date")
    search_fields = ("tyre_item__size", "tyre_item__brand", "remark", "bill_number")