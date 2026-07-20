import datetime
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.shortcuts import render, redirect

from .models import TyreItem, DailyEntry, BUCKET_CHOICES
from .forms import TyreItemForm, ProductionEntryForm, DispatchEntryForm, AdjustmentEntryForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("home")
    return render(request, "stock/login.html", {"form": form})



@login_required
def home(request):
    return render(request, "home.html")

def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    q = request.GET.get("q", "").strip()
    items = TyreItem.objects.filter(is_active=True)
    if q:
        items = items.filter(
            Q(tyre__icontains=q) | Q(pattern__icontains=q) | Q(type__icontains=q)
        )

    today = datetime.date.today()
    today_production = DailyEntry.objects.filter(entry_type="production", date=today).aggregate(t=Sum("quantity"))["t"] or 0
    today_dispatch = DailyEntry.objects.filter(entry_type="dispatch", date=today).aggregate(t=Sum("quantity"))["t"] or 0

    month_start = today.replace(day=1)
    
    for item in items:
        item.month_curing = DailyEntry.objects.filter(
            tyre_item=item, entry_type="production",
            date__gte=month_start, date__lte=today
        ).aggregate(t=Sum("quantity"))["t"] or 0
        item.month_despatch = DailyEntry.objects.filter(
            tyre_item=item, entry_type="dispatch",
            date__gte=month_start, date__lte=today
        ).aggregate(t=Sum("quantity"))["t"] or 0

   
    month_production = DailyEntry.objects.filter(entry_type="production", date__gte=month_start, date__lte=today).aggregate(t=Sum("quantity"))["t"] or 0
    month_dispatch = DailyEntry.objects.filter(entry_type="dispatch", date__gte=month_start, date__lte=today).aggregate(t=Sum("quantity"))["t"] or 0

    grand_total = sum(item.total_stock for item in items)
    total_stock_col = sum(item.stock for item in items)
    total_repair = sum(item.repair_tyre_stock for item in items)
    total_rfm = sum(item.rfm_ok_tyre for item in items)
    total_old = sum(item.old_tyres_2025 for item in items)
    total_hold = sum(item.on_hold_export for item in items)
    total_curing = sum(item.month_curing for item in items)
    total_despatch = sum(item.month_despatch for item in items)
    context = {
        "items": items,
        "q": q,
        "today": today,
        "today_production": today_production,
        "today_dispatch": today_dispatch,
        "month_production": month_production,
        "month_dispatch": month_dispatch,
        "grand_total": grand_total,
        "total_stock_col": total_stock_col,
        "total_repair": total_repair,
        "total_rfm": total_rfm,
        "total_old": total_old,
        "total_hold": total_hold,
        "total_curing": total_curing,
        "total_despatch": total_despatch,
    }
    return render(request, "stock/dashboard.html", context)


@login_required
def add_tyre(request):
    form = TyreItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.tyre = item.tyre.strip()
        item.pattern = item.pattern.strip()
        item.type = item.type.strip()
        item.save()
        messages.success(request, f"Tyre '{item}' add ho gaya.")
        return redirect("dashboard")
    return render(request, "stock/add_tyre.html", {"form": form})


@login_required
def add_production(request):
    form = ProductionEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            item = form.cleaned_data["tyre_item"]
            qty = form.cleaned_data["quantity"]
            item.stock += qty
            item.save(update_fields=["stock"])
            DailyEntry.objects.create(
                tyre_item=item,
                entry_type="production",
                bucket="stock",
                quantity=qty,
                date=form.cleaned_data["date"],
                remark=form.cleaned_data["remark"],
                user=request.user,
            )
        messages.success(request, f"Production entry has been added: {item} +{qty}")
        return redirect("add_production")
    recent = DailyEntry.objects.filter(entry_type="production").select_related("tyre_item", "user")[:15]
    return render(request, "stock/add_production.html", {"form": form, "recent": recent})


@login_required
def add_dispatch(request):
    form = DispatchEntryForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
            item = form.cleaned_data["tyre_item"]
            bucket = form.cleaned_data["bucket"]
            qty = form.cleaned_data["quantity"]
            bill_number = form.cleaned_data["bill_number"].strip()
            current = getattr(item, bucket)

            duplicate = DailyEntry.objects.filter(
                entry_type="dispatch", bill_number__iexact=bill_number
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
                    DailyEntry.objects.create(
                        tyre_item=item,
                        entry_type="dispatch",
                        bucket=bucket,
                        quantity=qty,
                        date=form.cleaned_data["date"],
                        bill_number=bill_number,
                        remark=form.cleaned_data["remark"],
                        user=request.user,
                    )
                messages.success(request, f"Dispatch entry has been added: {item} -{qty} ({dict(BUCKET_CHOICES)[bucket]}) | Bill: {bill_number}")
                return redirect("add_dispatch")
    recent = DailyEntry.objects.filter(entry_type="dispatch").select_related("tyre_item", "user")[:15]
    return render(request, "stock/add_dispatch.html", {"form": form, "recent": recent})


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
                DailyEntry.objects.create(
                    tyre_item=item,
                    entry_type="adjustment",
                    bucket=bucket,
                    quantity=signed_qty,
                    date=form.cleaned_data["date"],
                    remark=form.cleaned_data["remark"],
                    user=request.user,
                )
            messages.success(request, f"Adjustment ho gaya: {item} {signed_qty:+d} ({dict(BUCKET_CHOICES)[bucket]})")
            return redirect("add_adjustment")
    return render(request, "stock/add_adjustment.html", {"form": form})


@login_required
def entries_log(request):
    date_str = request.GET.get("date", "")
    month_str = request.GET.get("month", "")
    entry_type = request.GET.get("type", "")

    entries = DailyEntry.objects.select_related("tyre_item", "user")

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
    return render(request, "stock/entries_log.html", context)


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

    items = TyreItem.objects.filter(is_active=True)
    rows = []
    for item in items:
        production = DailyEntry.objects.filter(
            tyre_item=item, entry_type="production", date__year=year, date__month=month
        ).aggregate(t=Sum("quantity"))["t"] or 0
        dispatch = DailyEntry.objects.filter(
            tyre_item=item, entry_type="dispatch", date__year=year, date__month=month
        ).aggregate(t=Sum("quantity"))["t"] or 0
        if production or dispatch:
            rows.append({
                "item": item,
                "monthly_curing": production,
                "monthly_despatch": dispatch,
            })

    total_curing = sum(r["monthly_curing"] for r in rows)
    total_despatch = sum(r["monthly_despatch"] for r in rows)
    total_stock_col = sum(item.stock for item in items)
    grand_total = sum(item.total_stock for item in items)
    net_balance = total_curing - total_despatch

    selected_month_date = datetime.date(year, month, 1)
    month_name = selected_month_date.strftime("%B %Y")

    # Real 6-month trend (including the selected month), not fake/random data
    trend_labels, trend_production, trend_dispatch = [], [], []
    cursor_year, cursor_month = year, month
    months_back = []
    for _ in range(6):
        months_back.append((cursor_year, cursor_month))
        cursor_month -= 1
        if cursor_month == 0:
            cursor_month = 12
            cursor_year -= 1
    months_back.reverse()

    for y2, m2 in months_back:
        prod = DailyEntry.objects.filter(
            entry_type="production", date__year=y2, date__month=m2
        ).aggregate(t=Sum("quantity"))["t"] or 0
        disp = DailyEntry.objects.filter(
            entry_type="dispatch", date__year=y2, date__month=m2
        ).aggregate(t=Sum("quantity"))["t"] or 0
        trend_labels.append(datetime.date(y2, m2, 1).strftime("%b %Y"))
        trend_production.append(prod)
        trend_dispatch.append(disp)

    context = {
        "rows": rows,
        "month_value": f"{year:04d}-{month:02d}",
        "month_name": month_name,
        "total_curing": total_curing,
        "total_despatch": total_despatch,
        "total_stock_col": total_stock_col,
        "grand_total": grand_total,
        "net_balance": net_balance,
        "trend_labels": trend_labels,
        "trend_production": trend_production,
        "trend_dispatch": trend_dispatch,
    }
    return render(request, "stock/monthly_report.html", context)