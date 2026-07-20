from django.contrib import admin
from .models import *


@admin.register(MaterialGroup)
class MaterialGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "group",
        "unit",
        "minimum_stock",
    ]

    list_filter = ["group"]
    search_fields = ["name"]


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):

    list_display = [
        "date",
        "material",
        "opening",
        "received_quantity",
        "used_quantity",
        "closing",
        "created_by",
    ]

    list_filter = [
        "material__group",
        "material",
        "date",
    ]

    search_fields = [
        "material__name",
    ]