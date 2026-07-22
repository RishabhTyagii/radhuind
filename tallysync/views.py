import json
import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import TallyItemMapping, TallyInvoice, TallySyncLog, MODULE_CHOICES


def _to_decimal(value):
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _reduce_stock_for_item(module, item, qty, voucher_number, voucher_date, party_name):
    """Create a sale/dispatch entry for this item, reducing its STOCK bucket.
    Returns (ok: bool, message: str)."""
    if item is None:
        return False, "Mapped item not found in the module (was it deleted?)."

    current = item.stock
    if qty > current:
        return False, f"'{item}' ke STOCK mai sirf {current} hai, {qty} chahiye — stock manually check karo."

    remark = f"Tally auto-sync | Party: {party_name or '-'}"

    if module == "tyre":
        from stock.models import DailyEntry
        with transaction.atomic():
            item.stock = current - qty
            item.save(update_fields=["stock"])
            DailyEntry.objects.create(
                tyre_item=item, entry_type="dispatch", bucket="stock",
                quantity=qty, date=voucher_date, bill_number=voucher_number,
                remark=remark, user=None,
            )
    elif module == "tube":
        from cycletube.models import CycleTubeEntry
        with transaction.atomic():
            item.stock = current - qty
            item.save(update_fields=["stock"])
            CycleTubeEntry.objects.create(
                tube_item=item, entry_type="sale", bucket="stock",
                quantity=qty, date=voucher_date, bill_number=voucher_number,
                remark=remark, user=None,
            )
    elif module == "cycletyre":
        from cycletyres.models import CycleTyreEntry
        with transaction.atomic():
            item.stock = current - qty
            item.save(update_fields=["stock"])
            CycleTyreEntry.objects.create(
                tyre_item=item, entry_type="sale", bucket="stock",
                quantity=qty, date=voucher_date, bill_number=voucher_number,
                remark=remark, user=None,
            )
    else:
        return False, f"Unknown module '{module}'."

    return True, "ok"


@csrf_exempt
def tally_webhook(request):
    """Tally (via TDL) POSTs a Sales voucher here as JSON. Protected by API key header."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    api_key = request.headers.get("X-API-KEY", "")
    if not settings.TALLY_SYNC_API_KEY or api_key != settings.TALLY_SYNC_API_KEY:
        return JsonResponse({"error": "invalid api key"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid JSON body"}, status=400)

    voucher_number = str(payload.get("voucher_number", "")).strip()
    if not voucher_number:
        return JsonResponse({"error": "voucher_number is required"}, status=400)

    # Idempotency: if we've already processed this voucher, don't double-count stock.
    if TallyInvoice.objects.filter(voucher_number=voucher_number).exists():
        return JsonResponse({"status": "already_synced", "voucher_number": voucher_number}, status=200)

    try:
        voucher_date = datetime.datetime.strptime(payload.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        voucher_date = datetime.date.today()

    party_name = str(payload.get("party_name", "")).strip()
    items = payload.get("items", [])

    invoice = TallyInvoice.objects.create(
        voucher_number=voucher_number,
        voucher_date=voucher_date,
        party_name=party_name,
        taxable_value=_to_decimal(payload.get("taxable_value")),
        cgst=_to_decimal(payload.get("cgst")),
        sgst=_to_decimal(payload.get("sgst")),
        igst=_to_decimal(payload.get("igst")),
        total_value=_to_decimal(payload.get("total_value")),
        raw_payload=json.dumps(payload, indent=2),
    )

    all_ok = True
    results = []
    for line in items:
        tally_name = str(line.get("name", "")).strip()
        qty = int(line.get("qty", 0) or 0)

        mapping = TallyItemMapping.objects.filter(tally_item_name__iexact=tally_name).first()
        if not mapping:
            all_ok = False
            msg = f"Item '{tally_name}' mapped nahi hai — stock update nahi hua is item ke liye. Ise mapping page mein map karo."
            TallySyncLog.objects.create(invoice=invoice, level="warning", message=msg)
            results.append({"item": tally_name, "ok": False, "reason": "unmapped"})
            continue

        item = mapping.get_item()
        ok, msg = _reduce_stock_for_item(
            mapping.module, item, qty, voucher_number, voucher_date, party_name
        )
        if not ok:
            all_ok = False
            TallySyncLog.objects.create(invoice=invoice, level="error", message=msg)
        results.append({"item": tally_name, "ok": ok, "reason": msg})

    invoice.stock_synced = all_ok and len(items) > 0
    invoice.save(update_fields=["stock_synced"])

    if all_ok:
        TallySyncLog.objects.create(invoice=invoice, level="info", message="Sab items ka stock successfully update ho gaya.")

    return JsonResponse({"status": "processed", "voucher_number": voucher_number, "items": results})


@login_required
def sales_summary(request):
    month_str = request.GET.get("month", "")
    today = datetime.date.today()
    if month_str:
        try:
            y, m = month_str.split("-")
            year, month = int(y), int(m)
        except ValueError:
            year, month = today.year, today.month
    else:
        year, month = today.year, today.month

    invoices = TallyInvoice.objects.filter(voucher_date__year=year, voucher_date__month=month)

    total_sale = invoices.aggregate(t=Sum("total_value"))["t"] or 0
    total_taxable = invoices.aggregate(t=Sum("taxable_value"))["t"] or 0
    total_cgst = invoices.aggregate(t=Sum("cgst"))["t"] or 0
    total_sgst = invoices.aggregate(t=Sum("sgst"))["t"] or 0
    total_igst = invoices.aggregate(t=Sum("igst"))["t"] or 0
    total_gst = total_cgst + total_sgst + total_igst
    unmapped_count = invoices.filter(stock_synced=False).count()

    context = {
        "invoices": invoices.order_by("-voucher_date")[:200],
        "month_value": f"{year:04d}-{month:02d}",
        "total_sale": total_sale,
        "total_taxable": total_taxable,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_gst": total_gst,
        "unmapped_count": unmapped_count,
    }
    return render(request, "tallysync/sales_summary.html", context)


@login_required
def mapping_list(request):
    mappings = TallyItemMapping.objects.all()
    rows = []
    for m in mappings:
        item = m.get_item()
        rows.append({"mapping": m, "item": item})
    return render(request, "tallysync/mapping_list.html", {"rows": rows})


@login_required
def add_mapping(request):
    from stock.models import TyreItem
    from cycletube.models import CycleTubeItem
    from cycletyres.models import CycleTyreItem

    if request.method == "POST":
        tally_item_name = request.POST.get("tally_item_name", "").strip()
        item_choice = request.POST.get("item_choice", "")  # format: "module:id"
        if tally_item_name and ":" in item_choice:
            module, item_id = item_choice.split(":", 1)
            TallyItemMapping.objects.update_or_create(
                tally_item_name=tally_item_name,
                defaults={"module": module, "item_id": int(item_id)},
            )
            messages.success(request, f"Mapping save ho gayi: '{tally_item_name}' → {module} #{item_id}")
            return redirect("tally_mapping_list")
        else:
            messages.error(request, "Sabhi fields bharna zaroori hai.")

    context = {
        "tyre_items": TyreItem.objects.filter(is_active=True),
        "tube_items": CycleTubeItem.objects.filter(is_active=True),
        "cycletyre_items": CycleTyreItem.objects.filter(is_active=True),
    }
    return render(request, "tallysync/add_mapping.html", context)


@login_required
def sync_log(request):
    logs = TallySyncLog.objects.select_related("invoice")[:300]
    return render(request, "tallysync/sync_log.html", {"logs": logs})