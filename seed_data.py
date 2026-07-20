"""
Seed TyreItem master data from the latest snapshot found in the uploaded
Excel file (sheet: 'Auto Tyre Stock   (5)', dated 12/07/2026 - the most
recent sheet that has all 5 buckets: Repair Tyre Stock, RFM OK Tyre,
2025 Old Tyres, STOCK, On hold for Export/OR).

Run with:
    python3 manage.py shell < seed_data.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "radhu.settings")
django.setup()

import xlrd
from stock.models import TyreItem

XLS_PATH = "/mnt/user-data/uploads/Auto_Tyre_Daly_Stock_-_Copy.xls"
SHEET_NAME = "Auto Tyre Stock   (5)"


def to_int(v):
    if v == "" or v is None:
        return 0
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return 0


def run():
    wb = xlrd.open_workbook(XLS_PATH)
    sheet = wb.sheet_by_name(SHEET_NAME)

    created, updated = 0, 0
    for r in range(6, 59):  # data rows for Auto Tyre section
        row = [sheet.cell_value(r, c) for c in range(1, 12)]
        tyre = str(row[0]).strip()
        pattern = str(row[1]).strip()
        type_ = str(row[2]).strip()
        if not tyre or tyre.upper() == "TOTAL":
            continue

        repair = to_int(row[4])
        rfm_ok = to_int(row[5])
        old_2025 = to_int(row[6])
        stock_val = to_int(row[7])
        on_hold = to_int(row[8])

        obj, was_created = TyreItem.objects.update_or_create(
            tyre=tyre, pattern=pattern, type=type_,
            defaults=dict(
                repair_tyre_stock=repair,
                rfm_ok_tyre=rfm_ok,
                old_tyres_2025=old_2025,
                stock=stock_val,
                on_hold_export=on_hold,
            ),
        )
        created += 1 if was_created else 0
        updated += 0 if was_created else 1

    print(f"Seed complete. Created: {created}, Updated: {updated}, Total: {TyreItem.objects.count()}")


run()
