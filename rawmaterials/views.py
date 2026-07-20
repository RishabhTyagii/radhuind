from decimal import Decimal
from django.http import HttpResponse
from openpyxl import Workbook
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Q, Sum
from collections import OrderedDict
from .models import *
from .forms import *
from datetime import date, timedelta

@login_required
def dashboard(request):

    total_groups = MaterialGroup.objects.count()
    total_materials = Material.objects.count()
    total_entries = StockEntry.objects.count()

    context = {
        "total_groups": total_groups,
        "total_materials": total_materials,
        "total_entries": total_entries,
    }

    return render(
        request,
        "rawmaterials/dashboard.html",
        context
    )


@login_required
def new_entry(request):

    materials = Material.objects.select_related("group").all()

    if request.method == "POST":

        form = StockEntryForm(request.POST)

        if form.is_valid():

            obj = form.save(commit=False)

            previous = StockEntry.objects.filter(
                material=obj.material,
                date__lt=obj.date
            ).order_by("-date").first()

            if previous:
                obj.opening = previous.closing
            else:
                obj.opening = Decimal("0")

            obj.closing = (
                obj.opening
                + obj.received_quantity
                - obj.used_quantity
            )

            obj.created_by = request.user

            obj.save()

            messages.success(request, "Entry Saved")

            return redirect("raw_new_entry")

    else:

        form = StockEntryForm()

    return render(
        request,
        "rawmaterials/new_entry.html",
        {
            "form": form,
            "materials": materials,
        }
    )


@login_required
def entries(request):

    entries = StockEntry.objects.select_related(
        "material",
        "material__group",
        "created_by"
    ).order_by("-date")

    search = request.GET.get("q")

    if search:

        entries = entries.filter(

            Q(material__name__icontains=search)

            |

            Q(material__group__name__icontains=search)

        )

    return render(
        request,
        "rawmaterials/entries.html",
        {
            "entries": entries
        }
    )
    




@login_required
def low_stock(request):

    today = date.today()

    first_day_this_month = today.replace(day=1)

    last_month_last_day = first_day_this_month - timedelta(days=1)

    last_month_first_day = last_month_last_day.replace(day=1)

    days_in_last_month = last_month_last_day.day

    materials = Material.objects.select_related("group")

    data = []

    for material in materials:

        last = StockEntry.objects.filter(
            material=material
        ).order_by("-date", "-id").first()

        current_stock = last.closing if last else 0

        total_usage = StockEntry.objects.filter(
            material=material,
            date__gte=last_month_first_day,
            date__lte=last_month_last_day
        ).aggregate(
            total=Sum("used_quantity")
        )["total"] or 0

        avg = total_usage / days_in_last_month if days_in_last_month else 0

        days_left = current_stock / avg if avg else 999

        remaining_days = (
            today.replace(day=28) + timedelta(days=4)
        ).replace(day=1) - today

        status = "GOOD"

        if current_stock <= 0:
            status = "OUT"

        elif days_left < remaining_days.days:
            status = "LOW"

        data.append({

            "group": material.group.name,

            "material": material.name,

            "stock": current_stock,

            "usage": total_usage,

            "avg": round(avg,2),

            "days_left": round(days_left,1),

            "status": status,

            "unit": material.unit,

        })

    return render(
        request,
        "rawmaterials/low_stock.html",
        {
            "rows": data
        }
    )
    


@login_required
def current_stock(request):

    groups = MaterialGroup.objects.prefetch_related("materials").all()

    stock_data = OrderedDict()

    today = date.today()

    first_day_this_month = today.replace(day=1)
    last_month_last_day = first_day_this_month - timedelta(days=1)
    last_month_first_day = last_month_last_day.replace(day=1)

    days_in_last_month = last_month_last_day.day

    remaining_days = (
        (today.replace(day=28) + timedelta(days=4)).replace(day=1) - today
    ).days

    for group in groups:

        items = []

        for material in group.materials.all():

            last = (
                StockEntry.objects
                .filter(material=material)
                .order_by("-date", "-id")
                .first()
            )

            current = last.closing if last else 0

            last_month_usage = (
                StockEntry.objects.filter(
                    material=material,
                    date__range=(last_month_first_day, last_month_last_day)
                ).aggregate(
                    total=Sum("used_quantity")
                )["total"] or 0
            )

            avg_per_day = (
                last_month_usage / days_in_last_month
                if days_in_last_month else 0
            )

            days_left = (
                current / avg_per_day
                if avg_per_day else 999
            )

            if current <= 0:
                status = "OUT"
            elif days_left < remaining_days:
                status = "LOW"
            else:
                status = "OK"

            items.append({
                "material": material,
                "material_id": material.id,
                "unit": material.unit,
                "stock": current,
                "usage": round(last_month_usage, 2),
                "status": status,
            })

        stock_data[group] = items

    return render(
        request,
        "rawmaterials/current_stock.html",
        {
            "stock_data": stock_data
        }
    )
@login_required
def export_current_stock_excel(request):

    wb = Workbook()
    ws = wb.active
    ws.title = "Current Stock"

    ws.append([
        "Group",
        "Material",
        "Last Month Usage",
        "Current Closing",
        "Unit",
        "Status",
    ])

    today = date.today()

    first_day_this_month = today.replace(day=1)
    last_month_last_day = first_day_this_month - timedelta(days=1)
    last_month_first_day = last_month_last_day.replace(day=1)

    days_in_last_month = last_month_last_day.day

    remaining_days = (
        (today.replace(day=28) + timedelta(days=4)).replace(day=1) - today
    ).days

    groups = MaterialGroup.objects.prefetch_related("materials").all()

    for group in groups:

        for material in group.materials.all():

            last = (
                StockEntry.objects
                .filter(material=material)
                .order_by("-date", "-id")
                .first()
            )

            current = last.closing if last else 0

            last_month_usage = (
                StockEntry.objects.filter(
                    material=material,
                    date__range=(last_month_first_day, last_month_last_day)
                ).aggregate(
                    total=Sum("used_quantity")
                )["total"] or 0
            )

            avg = (
                last_month_usage / days_in_last_month
                if days_in_last_month else 0
            )

            days_left = (
                current / avg
                if avg else 999
            )

            if current <= 0:
                status = "OUT"
            elif days_left < remaining_days:
                status = "LOW"
            else:
                status = "OK"

            ws.append([
                group.name,
                material.name,
                float(last_month_usage),
                float(current),
                material.unit,
                status,
            ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Current_Stock_Report.xlsx"'
    )

    wb.save(response)

    return response



@login_required
def tally_view(request):

    form = TallyFilterForm(request.GET or None)

    entries = (
        StockEntry.objects
        .select_related(
            "material",
            "material__group",
            "created_by",
        )
        .order_by("date", "id")
    )

    material = None
    from_date = None
    to_date = None

    if form.is_valid():

        material = form.cleaned_data.get("material")
        from_date = form.cleaned_data.get("from_date")
        to_date = form.cleaned_data.get("to_date")

        if material:
            entries = entries.filter(material=material)

        if from_date:
            entries = entries.filter(date__gte=from_date)

        if to_date:
            entries = entries.filter(date__lte=to_date)

    context = {
        "form": form,
        "entries": entries,
        "material": material,
    }

    return render(
        request,
        "rawmaterials/tally.html",
        context,
    )