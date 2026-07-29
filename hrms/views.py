import json
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Department, Employee, Attendance, Production,
    Salary, Advance, Bonus, Deduction, LeaveBalance,
)
from .forms import (
    DepartmentForm, EmployeeForm, AttendanceForm,
    ProductionForm, AdvanceForm, BonusForm, DeductionForm,
)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# =====================================================
# Dashboard
# =====================================================

@login_required
def dashboard(request):
    today = date.today()
    total_employee = Employee.objects.filter(status="Active").count()
    total_department = Department.objects.count()
    today_attendance = Attendance.objects.filter(date=today).count()
    today_present = Attendance.objects.filter(date=today, status="Present").count()
    today_absent = Attendance.objects.filter(date=today, status="Absent").count()
    today_production = Production.objects.filter(date=today).aggregate(qty=Sum("quantity"))["qty"] or 0
    today_prod_amt = Production.objects.filter(date=today).aggregate(amt=Sum("total_amount"))["amt"] or 0
    month_start = today.replace(day=1)
    month_prod = Production.objects.filter(date__gte=month_start, date__lte=today).aggregate(amt=Sum("total_amount"))["amt"] or 0
    recent_attendance = Attendance.objects.select_related("employee").order_by("-date")[:10]

    context = {
        "total_employee": total_employee,
        "total_department": total_department,
        "today_attendance": today_attendance,
        "today_present": today_present,
        "today_absent": today_absent,
        "today_production": today_production,
        "today_prod_amt": today_prod_amt,
        "month_prod": month_prod,
        "recent_attendance": recent_attendance,
        "today": today,
    }
    return render(request, "hrms/dashboard.html", context)


# =====================================================
# Department
# =====================================================

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, "hrms/department_list.html", {"departments": departments})


@login_required
def department_add(request):
    form = DepartmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department added.")
        return redirect("department_list")
    return render(request, "hrms/department_form.html", {"form": form, "title": "Add Department"})


@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department updated.")
        return redirect("department_list")
    return render(request, "hrms/department_form.html", {"form": form, "title": "Edit Department"})


@login_required
def department_delete(request, pk):
    get_object_or_404(Department, pk=pk).delete()
    messages.success(request, "Department deleted.")
    return redirect("department_list")


# =====================================================
# Employee
# =====================================================

@login_required
def employee_list(request):
    search = request.GET.get("search", "").strip()
    dept_id = request.GET.get("department", "")
    emp_type = request.GET.get("emp_type", "")
    status_filter = request.GET.get("status", "Active")

    employees = Employee.objects.select_related("department")

    if status_filter:
        employees = employees.filter(status=status_filter)
    if search:
        employees = employees.filter(
            Q(name__icontains=search) | Q(employee_code__icontains=search) | Q(mobile__icontains=search)
        )
    if dept_id:
        employees = employees.filter(department_id=dept_id)
    if emp_type:
        employees = employees.filter(employee_type=emp_type)

    context = {
        "employees": employees,
        "departments": Department.objects.all(),
        "search": search,
        "dept_id": dept_id,
        "emp_type": emp_type,
        "status_filter": status_filter,
        "today": date.today(),
    }
    return render(request, "hrms/employee_list.html", context)


@login_required
def employee_add(request):
    form = EmployeeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        emp = form.save()
        LeaveBalance.objects.get_or_create(employee=emp, year=date.today().year, defaults={"cl_balance": 7, "el_balance": 13})
        messages.success(request, f"Employee '{emp.name}' added successfully.")
        return redirect("employee_list")
    return render(request, "hrms/employee_form.html", {"form": form, "title": "Add Employee"})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Employee updated.")
        return redirect("employee_detail", pk=pk)
    return render(request, "hrms/employee_form.html", {"form": form, "title": "Edit Employee", "employee": employee})


@login_required
def employee_delete(request, pk):
    get_object_or_404(Employee, pk=pk).delete()
    messages.success(request, "Employee deleted.")
    return redirect("employee_list")


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    today = date.today()

    month_str = request.GET.get("month", f"{today.year}-{today.month:02d}")
    try:
        y, m = month_str.split("-")
        year, month = int(y), int(m)
    except (ValueError, AttributeError):
        year, month = today.year, today.month

    # Attendance
    attendance_qs = Attendance.objects.filter(
        employee=employee, date__year=year, date__month=month
    ).order_by("date")

    present_days = attendance_qs.filter(status="Present").count()
    half_days = attendance_qs.filter(status="Half Day").count()
    absent_days = attendance_qs.filter(status="Absent").count()
    holiday_days = attendance_qs.filter(status="Holiday").count()
    weekoff_days = attendance_qs.filter(status="Week Off").count()
    cl_used = attendance_qs.filter(leave_type="CL").count()
    el_used = attendance_qs.filter(leave_type="EL").count()
    lop_days = attendance_qs.filter(leave_type="LOP").count()
    total_work_hrs = attendance_qs.aggregate(t=Sum("working_hours"))["t"] or Decimal("0")
    total_ot_hrs = attendance_qs.aggregate(t=Sum("overtime_hours"))["t"] or Decimal("0")

    # Leave Balance
    leave_balance = LeaveBalance.objects.filter(employee=employee, year=year).first()

    # Production
    production_qs = Production.objects.filter(
        employee=employee, date__year=year, date__month=month
    ).order_by("date", "product_name")

    total_prod_qty = production_qs.aggregate(t=Sum("quantity"))["t"] or Decimal("0")
    total_prod_amount = production_qs.aggregate(t=Sum("total_amount"))["t"] or Decimal("0")

    prod_by_date = {}
    for p in production_qs:
        prod_by_date.setdefault(p.date, []).append(p)

    # Salary
    salary = Salary.objects.filter(employee=employee, month=month, year=year).first()

    # Advances / Bonuses / Deductions
    advances = Advance.objects.filter(employee=employee, date__year=year, date__month=month)
    bonuses = Bonus.objects.filter(employee=employee, date__year=year, date__month=month)
    deductions = Deduction.objects.filter(employee=employee, date__year=year, date__month=month)

    total_advance = advances.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    total_bonus = bonuses.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    total_deduction = deductions.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    month_choices = []
    for i in range(12, 0, -1):
        month_choices.append({
            "value": f"{year}-{i:02d}",
            "label": f"{MONTH_NAMES[i]} {year}",
        })
    for i in range(12, 0, -1):
        month_choices.append({
            "value": f"{year-1}-{i:02d}",
            "label": f"{MONTH_NAMES[i]} {year-1}",
        })

    context = {
        "employee": employee,
        "month_str": month_str,
        "month_name": MONTH_NAMES[month],
        "year": year,
        "month": month,
        "month_choices": month_choices,
        "attendance_qs": attendance_qs,
        "present_days": present_days,
        "half_days": half_days,
        "absent_days": absent_days,
        "holiday_days": holiday_days,
        "weekoff_days": weekoff_days,
        "cl_used": cl_used,
        "el_used": el_used,
        "lop_days": lop_days,
        "total_work_hrs": total_work_hrs,
        "total_ot_hrs": total_ot_hrs,
        "leave_balance": leave_balance,
        "production_qs": production_qs,
        "prod_by_date": prod_by_date,
        "total_prod_qty": total_prod_qty,
        "total_prod_amount": total_prod_amount,
        "salary": salary,
        "advances": advances,
        "bonuses": bonuses,
        "deductions": deductions,
        "total_advance": total_advance,
        "total_bonus": total_bonus,
        "total_deduction": total_deduction,
    }
    return render(request, "hrms/employee_detail.html", context)


# =====================================================
# Attendance
# =====================================================

def _calc_hours(att):
    if att.working_hours and att.working_hours > Decimal("0"):
        att.overtime_hours = max(Decimal("0"), att.working_hours - Decimal("8"))
    elif att.in_time and att.out_time:
        start = datetime.combine(att.date, att.in_time)
        end = datetime.combine(att.date, att.out_time)
        if end <= start:
            return False
        hours = Decimal(str(round((end - start).total_seconds() / 3600, 2)))
        att.working_hours = hours
        att.overtime_hours = max(Decimal("0"), hours - Decimal("8"))
    else:
        if att.status == "Present":
            att.working_hours = Decimal("8")
            att.overtime_hours = Decimal("0")
        elif att.status == "Half Day":
            att.working_hours = Decimal("4")
            att.overtime_hours = Decimal("0")
        else:
            att.working_hours = Decimal("0")
            att.overtime_hours = Decimal("0")
    return True


def _apply_leave_deduction(att):
    if att.status != "Absent" or not att.leave_type:
        return
    if att.leave_type not in ("CL", "EL"):
        return
    lb, _ = LeaveBalance.objects.get_or_create(
        employee=att.employee,
        year=att.date.year,
        defaults={"cl_balance": 7, "el_balance": 13}
    )
    if att.leave_type == "CL" and lb.cl_balance > 0:
        lb.cl_balance -= 1
        lb.save()
    elif att.leave_type == "EL" and lb.el_balance > 0:
        lb.el_balance -= 1
        lb.save()
    else:
        att.leave_type = "LOP"


def _restore_leave(att):
    if att.status != "Absent" or att.leave_type not in ("CL", "EL"):
        return
    lb = LeaveBalance.objects.filter(employee=att.employee, year=att.date.year).first()
    if not lb:
        return
    if att.leave_type == "CL":
        lb.cl_balance = min(7, lb.cl_balance + 1)
    elif att.leave_type == "EL":
        lb.el_balance = min(13, lb.el_balance + 1)
    lb.save()


@login_required
def attendance_list(request):
    search = request.GET.get("search", "").strip()
    date_filter = request.GET.get("date", "")
    dept_id = request.GET.get("department", "")
    month_str = request.GET.get("month", "")

    qs = Attendance.objects.select_related("employee", "employee__department")

    if search:
        qs = qs.filter(
            Q(employee__name__icontains=search) | Q(employee__employee_code__icontains=search)
        )
    if date_filter:
        qs = qs.filter(date=date_filter)
    elif month_str:
        try:
            y, m = month_str.split("-")
            qs = qs.filter(date__year=int(y), date__month=int(m))
        except ValueError:
            pass
    if dept_id:
        qs = qs.filter(employee__department_id=dept_id)

    attendance_list = list(qs.order_by("-date", "employee__name")[:500])

    # Attach Production details for each attendance entry on that date
    if attendance_list:
        emp_ids = {a.employee_id for a in attendance_list}
        dates = {a.date for a in attendance_list}
        prods = Production.objects.filter(employee_id__in=emp_ids, date__in=dates)
        
        prod_map = {}
        for p in prods:
            key = (p.employee_id, p.date)
            prod_map.setdefault(key, []).append(p)

        for a in attendance_list:
            key = (a.employee_id, a.date)
            a.daily_productions = prod_map.get(key, [])
            a.daily_prod_qty = sum(p.quantity for p in a.daily_productions)
            a.daily_prod_amt = sum(p.total_amount for p in a.daily_productions)

    context = {
        "attendance": attendance_list,
        "search": search,
        "date_filter": date_filter,
        "month_str": month_str,
        "dept_id": dept_id,
        "departments": Department.objects.all(),
    }
    return render(request, "hrms/attendance_list.html", context)


@login_required
def attendance_add(request):
    today = date.today()
    form = AttendanceForm(request.POST or None, initial={"date": today})

    if request.method == "POST" and form.is_valid():
        att = form.save(commit=False)
        att.created_by = request.user

        ok = _calc_hours(att)
        if not ok:
            form.add_error("out_time", "Out Time must be after In Time.")
            return render(request, "hrms/attendance_form.html", {"form": form, "title": "Mark Attendance"})

        _apply_leave_deduction(att)
        att.save()
        messages.success(request, f"Attendance marked: {att.employee.name} — {att.get_status_display()} ({att.date})")
        return redirect("attendance_list")

    leave_balances = {}
    for emp in Employee.objects.filter(status="Active"):
        lb = LeaveBalance.objects.filter(employee=emp, year=today.year).first()
        leave_balances[emp.id] = {
            "cl": lb.cl_balance if lb else 7,
            "el": lb.el_balance if lb else 13,
        }

    return render(request, "hrms/attendance_form.html", {
        "form": form,
        "title": "Mark Attendance",
        "leave_balances": leave_balances,
    })


@login_required
def attendance_edit(request, pk):
    att = get_object_or_404(Attendance, pk=pk)
    old_leave_type = att.leave_type
    old_status = att.status

    form = AttendanceForm(request.POST or None, instance=att)
    if request.method == "POST" and form.is_valid():
        att_new = form.save(commit=False)
        ok = _calc_hours(att_new)
        if not ok:
            form.add_error("out_time", "Out Time must be after In Time.")
            return render(request, "hrms/attendance_form.html", {"form": form, "title": "Edit Attendance"})

        if old_status == "Absent" and old_leave_type in ("CL", "EL"):
            _restore_leave(att)
        _apply_leave_deduction(att_new)
        att_new.save()
        messages.success(request, "Attendance updated.")
        return redirect("attendance_list")

    return render(request, "hrms/attendance_form.html", {"form": form, "title": "Edit Attendance", "att": att})


@login_required
def attendance_delete(request, pk):
    att = get_object_or_404(Attendance, pk=pk)
    _restore_leave(att)
    att.delete()
    messages.success(request, "Attendance deleted.")
    return redirect("attendance_list")


# =====================================================
# Production
# =====================================================

@login_required
def production_list(request):
    search = request.GET.get("search", "").strip()
    date_filter = request.GET.get("date", "")
    month_str = request.GET.get("month", "")

    qs = Production.objects.select_related("employee", "employee__department")

    if search:
        qs = qs.filter(
            Q(employee__name__icontains=search) |
            Q(employee__employee_code__icontains=search) |
            Q(product_name__icontains=search)
        )
    if date_filter:
        qs = qs.filter(date=date_filter)
    elif month_str:
        try:
            y, m = month_str.split("-")
            qs = qs.filter(date__year=int(y), date__month=int(m))
        except ValueError:
            pass

    qs = qs.order_by("-date", "employee__name")[:500]

    total_qty = qs.aggregate(t=Sum("quantity"))["t"] or 0
    total_amount = qs.aggregate(t=Sum("total_amount"))["t"] or 0

    context = {
        "production": qs,
        "total_qty": total_qty,
        "total_amount": total_amount,
        "search": search,
        "date_filter": date_filter,
        "month_str": month_str,
    }
    return render(request, "hrms/production_list.html", context)


@login_required
def production_add(request):
    today = date.today()
    form = ProductionForm(request.POST or None, initial={"date": today})
    if request.method == "POST" and form.is_valid():
        prod = form.save(commit=False)
        prod.created_by = request.user
        prod.total_amount = Decimal(str(prod.quantity)) * Decimal(str(prod.rate))
        prod.save()
        messages.success(request, f"Production saved: {prod.employee.name} — {prod.product_name} × {prod.quantity} @ ₹{prod.rate}")
        return redirect("production_add")

    # Fetch last saved rates per product and per employee-product pair
    recent_prods = Production.objects.order_by("-created_at")[:100]
    last_rates_by_product = {}
    last_rates_by_emp_prod = {}
    for p in recent_prods:
        p_name = p.product_name.strip().lower()
        if p_name not in last_rates_by_product:
            last_rates_by_product[p_name] = str(p.rate)
        key = f"{p.employee_id}_{p_name}"
        if key not in last_rates_by_emp_prod:
            last_rates_by_emp_prod[key] = str(p.rate)

    recent = Production.objects.select_related("employee").order_by("-created_at")[:20]
    return render(request, "hrms/production_form.html", {
        "form": form,
        "title": "Add Production",
        "recent": recent,
        "last_rates_by_product_json": json.dumps(last_rates_by_product),
        "last_rates_by_emp_prod_json": json.dumps(last_rates_by_emp_prod),
    })


@login_required
def production_edit(request, pk):
    prod = get_object_or_404(Production, pk=pk)
    form = ProductionForm(request.POST or None, instance=prod)
    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.total_amount = Decimal(str(p.quantity)) * Decimal(str(p.rate))
        p.save()
        messages.success(request, "Production updated.")
        return redirect("production_list")
    return render(request, "hrms/production_form.html", {"form": form, "title": "Edit Production"})


@login_required
def production_delete(request, pk):
    get_object_or_404(Production, pk=pk).delete()
    messages.success(request, "Production deleted.")
    return redirect("production_list")


# =====================================================
# Advance / Bonus / Deduction
# =====================================================

@login_required
def advance_list(request):
    return render(request, "hrms/advance_list.html", {
        "advances": Advance.objects.select_related("employee").order_by("-date")
    })


@login_required
def advance_delete(request, pk):
    get_object_or_404(Advance, pk=pk).delete()
    messages.success(request, "Advance record deleted.")
    return redirect("advance_list")


@login_required
def advance_add(request):
    form = AdvanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Advance saved.")
        return redirect("advance_list")
    return render(request, "hrms/advance_form.html", {"form": form, "title": "Add Advance"})


@login_required
def bonus_list(request):
    return render(request, "hrms/bonus_list.html", {
        "bonus": Bonus.objects.select_related("employee").order_by("-date")
    })


@login_required
def bonus_delete(request, pk):
    get_object_or_404(Bonus, pk=pk).delete()
    messages.success(request, "Bonus record deleted.")
    return redirect("bonus_list")


@login_required
def bonus_add(request):
    form = BonusForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Bonus saved.")
        return redirect("bonus_list")
    return render(request, "hrms/bonus_form.html", {"form": form, "title": "Add Bonus"})


@login_required
def deduction_list(request):
    return render(request, "hrms/deduction_list.html", {
        "deductions": Deduction.objects.select_related("employee").order_by("-date")
    })


@login_required
def deduction_delete(request, pk):
    get_object_or_404(Deduction, pk=pk).delete()
    messages.success(request, "Deduction record deleted.")
    return redirect("deduction_list")


@login_required
def deduction_add(request):
    form = DeductionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Deduction saved.")
        return redirect("deduction_list")
    return render(request, "hrms/deduction_form.html", {"form": form, "title": "Add Deduction"})


# =====================================================
# Salary
# =====================================================

@login_required
def salary_list(request):
    search = request.GET.get("search", "").strip()
    month_str = request.GET.get("month", "")
    qs = Salary.objects.select_related("employee", "employee__department")
    if search:
        qs = qs.filter(
            Q(employee__name__icontains=search) | Q(employee__employee_code__icontains=search)
        )
    if month_str:
        try:
            y, m = month_str.split("-")
            qs = qs.filter(year=int(y), month=int(m))
        except ValueError:
            pass
    return render(request, "hrms/salary_list.html", {
        "salaries": qs.order_by("-year", "-month"),
        "search": search,
        "month_str": month_str,
    })


@login_required
def generate_salary(request):
    today = date.today()
    if request.method == "POST":
        employee_id = request.POST.get("employee")
        month = int(request.POST.get("month", today.month))
        year = int(request.POST.get("year", today.year))
        employee = get_object_or_404(Employee, pk=employee_id)

        att_qs = Attendance.objects.filter(employee=employee, date__month=month, date__year=year)
        total_days_in_month = monthrange(year, month)[1]
        present_days = att_qs.filter(status="Present").count()
        half_days = att_qs.filter(status="Half Day").count()
        lop_days = att_qs.filter(leave_type="LOP").count()
        total_ot = att_qs.aggregate(t=Sum("overtime_hours"))["t"] or Decimal("0")

        payable_days = Decimal(str(present_days)) + Decimal(str(half_days)) * Decimal("0.5")
        per_day = employee.basic_salary / Decimal(str(total_days_in_month)) if total_days_in_month else Decimal("0")
        basic_payable = round(per_day * payable_days, 2)

        production_amount = Production.objects.filter(
            employee=employee, date__month=month, date__year=year
        ).aggregate(t=Sum("total_amount"))["t"] or Decimal("0")

        overtime_amount = round(total_ot * employee.overtime_rate, 2)

        advance = Advance.objects.filter(employee=employee, date__month=month, date__year=year).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        bonus = Bonus.objects.filter(employee=employee, date__month=month, date__year=year).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        deduction = Deduction.objects.filter(employee=employee, date__month=month, date__year=year).aggregate(t=Sum("amount"))["t"] or Decimal("0")

        pf_amount = round(basic_payable * employee.pf_percent / 100, 2)
        esi_amount = round(basic_payable * employee.esi_percent / 100, 2)

        net_salary = basic_payable + overtime_amount + production_amount + bonus - advance - deduction - pf_amount - esi_amount

        Salary.objects.update_or_create(
            employee=employee, month=month, year=year,
            defaults={
                "basic_salary": basic_payable,
                "overtime_amount": overtime_amount,
                "production_amount": production_amount,
                "bonus": bonus,
                "advance": advance,
                "deduction": deduction,
                "pf_amount": pf_amount,
                "esi_amount": esi_amount,
                "net_salary": round(net_salary, 2),
            }
        )
        messages.success(request, f"Salary generated for {employee.name} — {MONTH_NAMES[month]} {year}.")
        return redirect("salary_slip_emp", employee_id=employee.pk, month=month, year=year)

    return render(request, "hrms/generate_salary.html", {
        "employees": Employee.objects.filter(status="Active").select_related("department"),
        "today": today,
        "months": [(i, MONTH_NAMES[i]) for i in range(1, 13)],
    })


@login_required
def salary_slip(request, pk):
    salary = get_object_or_404(Salary, pk=pk)
    return render(request, "hrms/salary_slip.html", {"salary": salary})


@login_required
def salary_slip_emp(request, employee_id, month, year):
    employee = get_object_or_404(Employee, pk=employee_id)
    salary = Salary.objects.filter(employee=employee, month=month, year=year).first()
    return render(request, "hrms/salary_slip.html", {
        "salary": salary,
        "employee": employee,
        "month_name": MONTH_NAMES[month],
        "year": year,
    })


@login_required
def employee_month_summary(request, employee_id, month, year):
    return redirect(f"/hrms/employees/{employee_id}/?month={year}-{month:02d}")