from django.contrib import admin
from .models import CycleTubeItem, CycleTubeEntry


@admin.register(CycleTubeItem)
class CycleTubeItemAdmin(admin.ModelAdmin):
    list_display = ("size", "type", "brand", "stock", "rfm_stock", "total_stock", "is_active")
    search_fields = ("size", "type", "brand")
    list_filter = ("type", "is_active")


@admin.register(CycleTubeEntry)
class CycleTubeEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "tube_item", "entry_type", "bucket", "quantity", "bill_number", "user", "remark")
    list_filter = ("entry_type", "bucket", "date")
    search_fields = ("tube_item__size", "tube_item__brand", "remark", "bill_number")