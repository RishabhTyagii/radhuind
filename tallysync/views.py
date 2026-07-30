import json
import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Sum , Q 
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import TallyItemMapping, TallyInvoice, TallySyncLog, TallyPendingItem, MODULE_CHOICES


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
       return False, f"Only {current} units of '{item}' are available in STOCK, but {qty} are required — please check the stock manually."

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


def _maybe_mark_invoice_synced(invoice):
    """If an invoice has no more unresolved pending items, mark it as fully synced."""
    still_pending = invoice.pending_items.filter(resolved=False).exists()
    if not still_pending and not invoice.stock_synced:
        invoice.stock_synced = True
        invoice.save(update_fields=["stock_synced"])


def retry_pending_items(tally_item_name=None):
    """Re-attempt any unresolved pending line items (unmapped or insufficient
    stock). Pass tally_item_name to scope the retry to just that item (fast,
    used right after a mapping is added); leave it None to retry everything
    (used opportunistically whenever the Tally webhook is pinged, so stock
    increases from Production entries get picked up automatically within a
    few minutes without touching the other 3 stock apps).
    Returns how many were resolved.
    """
    pending_qs = TallyPendingItem.objects.filter(resolved=False).select_related("invoice")
    if tally_item_name:
        pending_qs = pending_qs.filter(tally_item_name__iexact=tally_item_name)

    resolved_count = 0
    for pending in pending_qs:
        mapping = TallyItemMapping.objects.filter(tally_item_name__iexact=pending.tally_item_name).first()
        if not mapping:
            continue  # still unmapped, leave as pending

        item = mapping.get_item()
        ok, msg = _reduce_stock_for_item(
            mapping.module, item, pending.qty,
            pending.voucher_number, pending.voucher_date, pending.party_name,
        )
        if ok:
            pending.resolved = True
            pending.resolved_at = timezone.now()
            pending.save(update_fields=["resolved", "resolved_at"])
            TallySyncLog.objects.create(
                invoice=pending.invoice, level="info",
                message=f"Resolved on retry: '{pending.tally_item_name}' x{pending.qty} — stock has now been deducted."
            )
            _maybe_mark_invoice_synced(pending.invoice)
            resolved_count += 1
        # if still not ok (e.g. still insufficient stock), leave pending as-is;
        # it'll be tried again next time this function runs.

    return resolved_count


@csrf_exempt
def tally_webhook(request):
    """Tally (via the bridge script) POSTs a Sales voucher here as JSON.
    Protected by API key header."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    api_key = request.headers.get("X-API-KEY", "")
    if not settings.TALLY_SYNC_API_KEY or api_key != settings.TALLY_SYNC_API_KEY:
        return JsonResponse({"error": "invalid api key"}, status=403)

    # Opportunistic retry: since the bridge script pings us every few minutes
    # anyway, use each ping to also re-check any previously-pending items
    # (e.g. stock that has since been topped up via a Production entry).
    retry_pending_items()

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
        party_gstin=str(payload.get("party_gstin", "")).strip(),
        party_address=str(payload.get("party_address", "")).strip(),
        consignee_name=str(payload.get("consignee_name", "")).strip(),
        consignee_gstin=str(payload.get("consignee_gstin", "")).strip(),
        place_of_supply=str(payload.get("place_of_supply", "")).strip(),
        state_name=str(payload.get("state_name", "")).strip(),
        gst_registration_type=str(payload.get("gst_registration_type", "")).strip(),
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
            msg = f"Item '{tally_name}' is not mapped — stock was not updated for this item. Please map it from the Mapping page."
            TallySyncLog.objects.create(invoice=invoice, level="warning", message=msg)
            TallyPendingItem.objects.create(
                invoice=invoice, tally_item_name=tally_name, qty=qty,
                voucher_number=voucher_number, voucher_date=voucher_date,
                party_name=party_name, reason="unmapped",
            )
            results.append({"item": tally_name, "ok": False, "reason": "unmapped"})
            continue

        item = mapping.get_item()
        ok, msg = _reduce_stock_for_item(
            mapping.module, item, qty, voucher_number, voucher_date, party_name
        )
        if not ok:
            all_ok = False
            TallySyncLog.objects.create(invoice=invoice, level="error", message=msg)
            TallyPendingItem.objects.create(
                invoice=invoice, tally_item_name=tally_name, qty=qty,
                voucher_number=voucher_number, voucher_date=voucher_date,
                party_name=party_name, reason="insufficient_stock",
            )
        results.append({"item": tally_name, "ok": ok, "reason": msg})

    invoice.stock_synced = all_ok and len(items) > 0
    invoice.save(update_fields=["stock_synced"])

    if all_ok:
        TallySyncLog.objects.create(invoice=invoice, level="info", message="*args* All items processed successfully, stock updated.")

    return JsonResponse({"status": "processed", "voucher_number": voucher_number, "items": results})


@login_required
def retry_pending_now(request):
    """Manual 'Retry Pending Now' button on the Sync Log page."""
    count = retry_pending_items()
    if count:
        messages.success(request, f"{count} pending item(s) resolve ho gaye aur stock update ho gaya!")
    else:
        messages.info(request, "No pending item has been resolved yet (either the mapping is still missing, or the stock is still low).")
    return redirect("tally_sync_log")


@login_required
def retry_single_pending(request, pk):
    """Manually retry ONE specific pending item (button next to each row)."""
    pending = get_object_or_404(TallyPendingItem, pk=pk)

    if pending.resolved:
        messages.info(request, "This item was already resolved earlier.")
        return redirect("tally_sync_log")

    mapping = TallyItemMapping.objects.filter(tally_item_name__iexact=pending.tally_item_name).first()
    if not mapping:
        messages.error(request, f"'{pending.tally_item_name}' is not mapped — please map it from the Mapping page.")
        return redirect("tally_sync_log")

    item = mapping.get_item()
    ok, msg = _reduce_stock_for_item(
        mapping.module, item, pending.qty,
        pending.voucher_number, pending.voucher_date, pending.party_name,
    )
    if ok:
        pending.resolved = True
        pending.resolved_at = timezone.now()
        pending.save(update_fields=["resolved", "resolved_at"])
        TallySyncLog.objects.create(
            invoice=pending.invoice, level="info",
            message=f"Manual retry se resolve ho gaya: '{pending.tally_item_name}' x{pending.qty}.",
        )
        _maybe_mark_invoice_synced(pending.invoice)
        messages.success(request, f"'{pending.tally_item_name}' x{pending.qty} It has been resolved — the stock has been updated.")
    else:
        messages.error(request, msg)

    return redirect("tally_sync_log")


@login_required
def sales_summary(request):
    month_str = request.GET.get("month", "").strip()
    from_date_str = request.GET.get("from_date", "").strip()
    to_date_str = request.GET.get("to_date", "").strip()
    party_query = request.GET.get("party", "").strip()
    today = datetime.date.today()

    invoices = TallyInvoice.objects.all()
    month_value = ""

    if from_date_str or to_date_str:
        # Date-range mode takes priority over the month picker when used.
        if from_date_str:
            try:
                from_date = datetime.datetime.strptime(from_date_str, "%Y-%m-%d").date()
                invoices = invoices.filter(voucher_date__gte=from_date)
            except ValueError:
                from_date_str = ""
        if to_date_str:
            try:
                to_date = datetime.datetime.strptime(to_date_str, "%Y-%m-%d").date()
                invoices = invoices.filter(voucher_date__lte=to_date)
            except ValueError:
                to_date_str = ""
    else:
        if month_str:
            try:
                y, m = month_str.split("-")
                year, month = int(y), int(m)
            except ValueError:
                year, month = today.year, today.month
        else:
            year, month = today.year, today.month
        invoices = invoices.filter(voucher_date__year=year, voucher_date__month=month)
        month_value = f"{year:04d}-{month:02d}"

    if party_query:
        invoices = invoices.filter(
            Q(party_name__icontains=party_query) |
            Q(voucher_number__icontains=party_query) |
            Q(party_gstin__icontains=party_query)
        )

    total_sale = invoices.aggregate(t=Sum("total_value"))["t"] or 0
    total_taxable = invoices.aggregate(t=Sum("taxable_value"))["t"] or 0
    total_cgst = invoices.aggregate(t=Sum("cgst"))["t"] or 0
    total_sgst = invoices.aggregate(t=Sum("sgst"))["t"] or 0
    total_igst = invoices.aggregate(t=Sum("igst"))["t"] or 0
    total_gst = total_cgst + total_sgst + total_igst
    unmapped_count = invoices.filter(stock_synced=False).count()
    invoice_count = invoices.count()

    invoices = invoices.order_by("-voucher_date", "-pk")
    paginator = Paginator(invoices, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "invoices": page_obj,
        "page_obj": page_obj,
        "month_value": month_value,
        "from_date": from_date_str,
        "to_date": to_date_str,
        "party_query": party_query,
        "total_sale": total_sale,
        "total_taxable": total_taxable,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_gst": total_gst,
        "unmapped_count": unmapped_count,
        "invoice_count": invoice_count,
    }
    return render(request, "tallysync/sales_summary.html", context)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(TallyInvoice, pk=pk)
    items = []
    try:
        payload = json.loads(invoice.raw_payload or "{}")
        items = payload.get("items", [])
    except json.JSONDecodeError:
        items = []
    pending_items = invoice.pending_items.all()
    return render(request, "tallysync/invoice_detail.html", {"invoice": invoice, "items": items, "pending_items": pending_items})


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
            # Instantly retry any pending items waiting on this exact item name.
            resolved = retry_pending_items(tally_item_name=tally_item_name)
            if resolved:
                messages.success(
                    request,
                    f"Mapping save ho gayi: '{tally_item_name}' → {module} #{item_id}. "
                    f"Saath hi {resolved} The pending item has also been resolved, and the stock has been updated."
                )
            else:
                messages.success(request, f"Mapping save ho gayi: '{tally_item_name}' → {module} #{item_id}")
            next_url = request.POST.get("next", "").strip()
            return redirect(next_url) if next_url else redirect("tally_mapping_list")
        else:
            messages.error(request, "Sabhi fields bharna zaroori hai.")

    context = {
        "tyre_items": TyreItem.objects.filter(is_active=True),
        "tube_items": CycleTubeItem.objects.filter(is_active=True),
        "cycletyre_items": CycleTyreItem.objects.filter(is_active=True),
        "prefill_name": request.GET.get("name", ""),
    }
    return render(request, "tallysync/add_mapping.html", context)


@login_required
def sync_log(request):
    from stock.models import TyreItem
    from cycletube.models import CycleTubeItem
    from cycletyres.models import CycleTyreItem

    logs_qs = TallySyncLog.objects.select_related("invoice")
    paginator = Paginator(logs_qs, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    pending_qs = TallyPendingItem.objects.filter(resolved=False).select_related("invoice")
    pending_paginator = Paginator(pending_qs, 20)
    pending_page_obj = pending_paginator.get_page(request.GET.get("ppage"))

    return render(request, "tallysync/sync_log.html", {
        "logs": page_obj,
        "page_obj": page_obj,
        "pending": pending_page_obj,
        "pending_page_obj": pending_page_obj,
        "pending_total": pending_qs.count(),
        "tyre_items": TyreItem.objects.filter(is_active=True),
        "tube_items": CycleTubeItem.objects.filter(is_active=True),
        "cycletyre_items": CycleTyreItem.objects.filter(is_active=True),
    })


@login_required
def map_pending_item(request, pk):
    """Inline 'map & sync' dropdown+button sitting right next to a pending row:
    Supports:
      - 'permanent' (default): creates/updates TallyItemMapping AND resolves pending item(s)
      - 'one_time': resolves this pending item NOW & deducts stock WITHOUT saving permanent mapping
    """
    pending = get_object_or_404(TallyPendingItem, pk=pk)

    if request.method != "POST":
        return redirect("tally_sync_log")

    item_choice = request.POST.get("item_choice", "")
    mapping_type = request.POST.get("mapping_type", "permanent").strip()

    if ":" not in item_choice:
        messages.error(request, "Pehle dropdown se ek item select karo.")
        return redirect("tally_sync_log")

    module, item_id_str = item_choice.split(":", 1)
    try:
        item_id = int(item_id_str)
    except ValueError:
        messages.error(request, "Invalid item selected.")
        return redirect("tally_sync_log")

    if mapping_type == "one_time":
        # -------------------------------------------------------------
        # ONE-TIME RESOLVE (This time only — no permanent mapping saved)
        # -------------------------------------------------------------
        from stock.models import TyreItem
        from cycletube.models import CycleTubeItem
        from cycletyres.models import CycleTyreItem

        target_item = None
        if module == "tyre":
            target_item = TyreItem.objects.filter(pk=item_id).first()
        elif module == "tube":
            target_item = CycleTubeItem.objects.filter(pk=item_id).first()
        elif module == "cycletyre":
            target_item = CycleTyreItem.objects.filter(pk=item_id).first()

        if not target_item:
            messages.error(request, "Selected item is invalid or was deleted.")
            return redirect("tally_sync_log")

        ok, msg = _reduce_stock_for_item(
            module, target_item, pending.qty,
            pending.voucher_number, pending.voucher_date, pending.party_name,
        )
        if ok:
            pending.resolved = True
            pending.resolved_at = timezone.now()
            pending.save(update_fields=["resolved", "resolved_at"])
            TallySyncLog.objects.create(
                invoice=pending.invoice, level="info",
                message=f"1-Time Sync (This time only): '{pending.tally_item_name}' x{pending.qty} mapped to {target_item}. Stock deducted without saving permanent mapping."
            )
            _maybe_mark_invoice_synced(pending.invoice)
            messages.success(
                request,
                f"⚡ '{pending.tally_item_name}' x{pending.qty} is bar ke liye resolve ho gaya aur stock minus ho gaya! (Permanent mapping nahi bani)."
            )
        else:
            messages.error(request, msg)

    else:
        # -------------------------------------------------------------
        # PERMANENT MAPPING (Save mapping rule + sync stock)
        # -------------------------------------------------------------
        TallyItemMapping.objects.update_or_create(
            tally_item_name=pending.tally_item_name,
            defaults={"module": module, "item_id": item_id},
        )

        resolved = retry_pending_items(tally_item_name=pending.tally_item_name)
        if resolved:
            messages.success(
                request,
                f"📌 '{pending.tally_item_name}' permanent map ho gaya — {resolved} pending item turant resolve ho gaya, stock update ho gaya!"
            )
        else:
            messages.warning(
                request,
                f"📌 '{pending.tally_item_name}' permanent map ho gaya, lekin stock abhi kam hai."
            )

    return redirect("tally_sync_log")