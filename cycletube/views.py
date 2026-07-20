import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.shortcuts import render, redirect

from .models import CycleTubeItem, CycleTubeEntry, BUCKET_CHOICES
from .forms import CycleTubeItemForm, ProductionEntryForm, SaleEntryForm, AdjustmentEntryForm


@login_required
def dashboard(request):
    q = request.GET.get("q", "").strip()
    items = CycleTubeItem.objects.filter(is_active=True)
    if q:
        items = items.filter(
            Q(size__icontains=q) | Q(type__icontains=q) | Q(brand__icontains=q)
        )

    today = datetime.date.today()
    today_production = CycleTubeEntry.objects.filter(entry_type="production", date=today).aggregate(t=Sum("quantity"))["t"] or 0
    today_sale = CycleTubeEntry.objects.filter(entry_type="sale", date=today).aggregate(t=Sum("quantity"))["t"] or 0

    month_start = today.replace(day=1)
    month_production = CycleTubeEntry.objects.filter(entry_type="production", date__gte=month_start, date__lte=today).aggregate(t=Sum("quantity"))["t"] or 0
    month_sale = CycleTubeEntry.objects.filter(entry_type="sale", date__gte=month_start, date__lte=today).aggregate(t=Sum("quantity"))["t"] or 0

    for item in items:
        item.month_production = CycleTubeEntry.objects.filter(
            tube_item=item, entry_type="production", date__gte=month_start, date__lte=today
        ).aggregate(t=Sum("quantity"))["t"] or 0
        item.month_sale = CycleTubeEntry.objects.filter(
            tube_item=item, entry_type="sale", date__gte=month_start, date__lte=today
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
    return render(request, "cycletube/dashboard.html", context)


@login_required
def add_item(request):
    form = CycleTubeItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.size = item.size.strip()
        item.type = item.type.strip()
        item.brand = item.brand.strip()
        item.save()
        messages.success(request, f"Cycle Tube '{item}' add ho gaya.")
        return redirect("tube_dashboard")
    return render(request, "cycletube/add_item.html", {"form": form})


@login_required
def add_production(request):
    form = ProductionEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            item = form.cleaned_data["tube_item"]
            qty = form.cleaned_data["quantity"]
            item.stock += qty
            item.save(update_fields=["stock"])
            CycleTubeEntry.objects.create(
                tube_item=item,
                entry_type="production",
                bucket="stock",
                quantity=qty,
                date=form.cleaned_data["date"],
                remark=form.cleaned_data["remark"],
                user=request.user,
            )
        messages.success(request, f"Production entry has been added: {item} +{qty}")
        return redirect("tube_add_production")
    recent = CycleTubeEntry.objects.filter(entry_type="production").select_related("tube_item", "user")[:15]
    return render(request, "cycletube/add_production.html", {"form": form, "recent": recent})


@login_required
def add_sale(request):
    form = SaleEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["tube_item"]
        bucket = form.cleaned_data["bucket"]
        qty = form.cleaned_data["quantity"]
        bill_number = form.cleaned_data["bill_number"].strip()
        current = getattr(item, bucket)

        duplicate = CycleTubeEntry.objects.filter(
            entry_type="sale", bill_number__iexact=bill_number
        ).first()

        if duplicate:
            messages.error(
                request,
                f"Bill number '{bill_number}' Already exists in sale entry: "
                f"({duplicate.date} - {duplicate.tube_item}). Duplicate Entry not allowed, "
                f"bill number check kar lo."
            )
        elif qty > current:
            messages.error(request, f"'{item}' ke '{dict(BUCKET_CHOICES)[bucket]}' bucket mai sirf {current} hi available hai.")
        else:
            with transaction.atomic():
                setattr(item, bucket, current - qty)
                item.save(update_fields=[bucket])
                CycleTubeEntry.objects.create(
                    tube_item=item,
                    entry_type="sale",
                    bucket=bucket,
                    quantity=qty,
                    date=form.cleaned_data["date"],
                    bill_number=bill_number,
                    remark=form.cleaned_data["remark"],
                    user=request.user,
                )
            messages.success(request, f"Sale entry has been added: {item} -{qty} ({dict(BUCKET_CHOICES)[bucket]}) | Bill: {bill_number}")
            return redirect("tube_add_sale")
    recent = CycleTubeEntry.objects.filter(entry_type="sale").select_related("tube_item", "user")[:15]
    return render(request, "cycletube/add_sale.html", {"form": form, "recent": recent})


@login_required
def add_adjustment(request):
    form = AdjustmentEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["tube_item"]
        bucket = form.cleaned_data["bucket"]
        action = form.cleaned_data["action"]
        qty = form.cleaned_data["quantity"]
        current = getattr(item, bucket)
        if action == "subtract" and qty > current:
            messages.error(request, f"'{item}' ke '{dict(BUCKET_CHOICES)[bucket]}' Only {current} Items are available in Bucket.")
        else:
            signed_qty = qty if action == "add" else -qty
            with transaction.atomic():
                setattr(item, bucket, current + signed_qty)
                item.save(update_fields=[bucket])
                CycleTubeEntry.objects.create(
                    tube_item=item,
                    entry_type="adjustment",
                    bucket=bucket,
                    quantity=signed_qty,
                    date=form.cleaned_data["date"],
                    remark=form.cleaned_data["remark"],
                    user=request.user,
                )
            messages.success(request, f"Adjustment has been added: {item} {signed_qty:+d} ({dict(BUCKET_CHOICES)[bucket]})")
            return redirect("tube_add_adjustment")
    return render(request, "cycletube/add_adjustment.html", {"form": form})


@login_required
def entries_log(request):
    date_str = request.GET.get("date", "")
    month_str = request.GET.get("month", "")
    entry_type = request.GET.get("type", "")

    entries = CycleTubeEntry.objects.select_related("tube_item", "user")

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
    return render(request, "cycletube/entries_log.html", context)


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

    items = CycleTubeItem.objects.filter(is_active=True)
    rows = []
    
    # Initialize totals
    total_production = 0
    total_sale = 0
    total_stock = 0
    grand_total = 0

    for item in items:
        production = CycleTubeEntry.objects.filter(
            tube_item=item, entry_type="production", date__year=year, date__month=month
        ).aggregate(t=Sum("quantity"))["t"] or 0
        sale = CycleTubeEntry.objects.filter(
            tube_item=item, entry_type="sale", date__year=year, date__month=month
        ).aggregate(t=Sum("quantity"))["t"] or 0
        
        if production or sale:
            rows.append({
                "item": item,
                "monthly_production": production,
                "monthly_sale": sale,
            })
            total_production += production
            total_sale += sale
            total_stock += item.stock
            grand_total += item.total_stock

    # Month name for display
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    month_name = f"{month_names[month-1]} {year}"

    context = {
        "rows": rows,
        "month_value": f"{year:04d}-{month:02d}",
        "month_name": month_name,
        "total_production": total_production,
        "total_sale": total_sale,
        "total_stock": total_stock,
        "grand_total": grand_total,
        "net_balance": total_production - total_sale,
    }
    return render(request, "cycletube/monthly_report.html", context)