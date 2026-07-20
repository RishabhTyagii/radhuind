import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.shortcuts import render, redirect

from .models import CycleTyreItem, CycleTyreEntry, BUCKET_CHOICES
from .forms import CycleTyreItemForm, ProductionEntryForm, SaleEntryForm, AdjustmentEntryForm


@login_required
def dashboard(request):
    q = request.GET.get("q", "").strip()
    items = CycleTyreItem.objects.filter(is_active=True)
    if q:
        items = items.filter(
            Q(size__icontains=q) | Q(box_type__icontains=q) | Q(material__icontains=q) | Q(brand__icontains=q)
        )

    today = datetime.date.today()
    today_production = CycleTyreEntry.objects.filter(entry_type="production", date=today).aggregate(t=Sum("quantity"))["t"] or 0
    today_sale = CycleTyreEntry.objects.filter(entry_type="sale", date=today).aggregate(t=Sum("quantity"))["t"] or 0

    month_start = today.replace(day=1)
    month_production = CycleTyreEntry.objects.filter(entry_type="production", date__gte=month_start, date__lte=today).aggregate(t=Sum("quantity"))["t"] or 0
    month_sale = CycleTyreEntry.objects.filter(entry_type="sale", date__gte=month_start, date__lte=today).aggregate(t=Sum("quantity"))["t"] or 0

    for item in items:
        item.month_production = CycleTyreEntry.objects.filter(
            tyre_item=item, entry_type="production", date__gte=month_start, date__lte=today
        ).aggregate(t=Sum("quantity"))["t"] or 0
        item.month_sale = CycleTyreEntry.objects.filter(
            tyre_item=item, entry_type="sale", date__gte=month_start, date__lte=today
        ).aggregate(t=Sum("quantity"))["t"] or 0

    grand_total = sum(item.total_stock for item in items)
    total_stock_col = sum(item.stock for item in items)
    total_rfm_col = sum(item.rfm_stock for item in items)

    context = {
        "items": items,
        "q": q,
        "today": today,
        "today_production": today_production,
        "today_sale": today_sale,
        "month_production": month_production,
        "month_sale": month_sale,
        "grand_total": grand_total,
        "total_stock_col": total_stock_col,
        "total_rfm_col": total_rfm_col,
    }
    return render(request, "cycletyres/dashboard.html", context)


@login_required
def add_item(request):
    form = CycleTyreItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.box_type = item.box_type.strip()
        item.size = item.size.strip()
        item.material = item.material.strip()
        item.brand = item.brand.strip()
        item.save()
        messages.success(request, f"Cycle Tyre '{item}' add ho gaya.")
        return redirect("cycletyre_dashboard")
    return render(request, "cycletyres/add_item.html", {"form": form})


@login_required
def add_production(request):
    form = ProductionEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            item = form.cleaned_data["tyre_item"]
            qty = form.cleaned_data["quantity"]
            item.stock += qty
            item.save(update_fields=["stock"])
            CycleTyreEntry.objects.create(
                tyre_item=item,
                entry_type="production",
                bucket="stock",
                quantity=qty,
                date=form.cleaned_data["date"],
                remark=form.cleaned_data["remark"],
                user=request.user,
            )
        messages.success(request, f"Production entry ho gayi: {item} +{qty}")
        return redirect("cycletyre_add_production")
    recent = CycleTyreEntry.objects.filter(entry_type="production").select_related("tyre_item", "user")[:15]
    return render(request, "cycletyres/add_production.html", {"form": form, "recent": recent})


@login_required
def add_sale(request):
    form = SaleEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["tyre_item"]
        bucket = form.cleaned_data["bucket"]
        qty = form.cleaned_data["quantity"]
        bill_number = form.cleaned_data["bill_number"].strip()
        current = getattr(item, bucket)

        duplicate = CycleTyreEntry.objects.filter(
            entry_type="sale", bill_number__iexact=bill_number
        ).first()

        if duplicate:
            messages.error(
                request,
                f"Bill number '{bill_number}' pehle se use ho chuka hai "
                f"({duplicate.date} - {duplicate.tyre_item}). Dubara save nahi hoga, "
                f"bill number check kar lo."
            )
        elif qty > current:
            messages.error(request, f"'{item}' ke '{dict(BUCKET_CHOICES)[bucket]}' bucket mai sirf {current} hi available hai.")
        else:
            with transaction.atomic():
                setattr(item, bucket, current - qty)
                item.save(update_fields=[bucket])
                CycleTyreEntry.objects.create(
                    tyre_item=item,
                    entry_type="sale",
                    bucket=bucket,
                    quantity=qty,
                    date=form.cleaned_data["date"],
                    bill_number=bill_number,
                    remark=form.cleaned_data["remark"],
                    user=request.user,
                )
            messages.success(request, f"Sale entry ho gayi: {item} -{qty} ({dict(BUCKET_CHOICES)[bucket]}) | Bill: {bill_number}")
            return redirect("cycletyre_add_sale")
    recent = CycleTyreEntry.objects.filter(entry_type="sale").select_related("tyre_item", "user")[:15]
    return render(request, "cycletyres/add_sale.html", {"form": form, "recent": recent})


@login_required
def add_adjustment(request):
    form = AdjustmentEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["tyre_item"]
        bucket = form.cleaned_data["bucket"]
        action = form.cleaned_data["action"]
        qty = form.cleaned_data["quantity"]
        current = getattr(item, bucket)
        if action == "subtract" and qty > current:
            messages.error(request, f"'{item}' ke '{dict(BUCKET_CHOICES)[bucket]}' bucket mai sirf {current} hi available hai.")
        else:
            signed_qty = qty if action == "add" else -qty
            with transaction.atomic():
                setattr(item, bucket, current + signed_qty)
                item.save(update_fields=[bucket])
                CycleTyreEntry.objects.create(
                    tyre_item=item,
                    entry_type="adjustment",
                    bucket=bucket,
                    quantity=signed_qty,
                    date=form.cleaned_data["date"],
                    remark=form.cleaned_data["remark"],
                    user=request.user,
                )
            messages.success(request, f"Adjustment ho gaya: {item} {signed_qty:+d} ({dict(BUCKET_CHOICES)[bucket]})")
            return redirect("cycletyre_add_adjustment")
    return render(request, "cycletyres/add_adjustment.html", {"form": form})


@login_required
def entries_log(request):
    date_str = request.GET.get("date", "")
    month_str = request.GET.get("month", "")
    entry_type = request.GET.get("type", "")

    entries = CycleTyreEntry.objects.select_related("tyre_item", "user")

    if date_str:
        try:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            entries = entries.filter(date=d)
        except ValueError:
            pass
    elif month_str:
        try:
            y, m = month_str.split("-")
            entries = entries.filter(date__year=int(y), date__month=int(m))
        except ValueError:
            pass

    if entry_type:
        entries = entries.filter(entry_type=entry_type)

    entries = entries[:500]

    context = {
        "entries": entries,
        "date_str": date_str,
        "month_str": month_str,
        "entry_type": entry_type,
    }
    return render(request, "cycletyres/entries_log.html", context)


@login_required
def monthly_report(request):
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

    items = CycleTyreItem.objects.filter(is_active=True)
    rows = []
    for item in items:
        production = CycleTyreEntry.objects.filter(
            tyre_item=item, entry_type="production", date__year=year, date__month=month
        ).aggregate(t=Sum("quantity"))["t"] or 0
        sale = CycleTyreEntry.objects.filter(
            tyre_item=item, entry_type="sale", date__year=year, date__month=month
        ).aggregate(t=Sum("quantity"))["t"] or 0
        if production or sale:
            rows.append({
                "item": item,
                "monthly_production": production,
                "monthly_sale": sale,
            })

    context = {
        "rows": rows,
        "month_value": f"{year:04d}-{month:02d}",
    }
    return render(request, "cycletyres/monthly_report.html", context)