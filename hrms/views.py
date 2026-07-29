from decimal import Decimal
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Department,
    Employee,
    Attendance,
    Production,
    Salary,
    Advance,
    Bonus,
    Deduction,
)

from .forms import (
    DepartmentForm,
    EmployeeForm,
    AttendanceForm,
    ProductionForm,
    AdvanceForm,
    BonusForm,
    DeductionForm,
)


# =====================================================
# Dashboard
# =====================================================

@login_required
def dashboard(request):

    total_employee = Employee.objects.filter(status="Active").count()

    total_department = Department.objects.count()

    today_attendance = Attendance.objects.filter(
        date=date.today()
    ).count()

    today_production = (
        Production.objects.filter(
            date=date.today()
        ).aggregate(
            qty=Sum("quantity")
        )["qty"] or 0
    )

    total_salary = (
        Salary.objects.aggregate(
            total=Sum("net_salary")
        )["total"] or 0
    )

    context = {

        "total_employee": total_employee,

        "total_department": total_department,

        "today_attendance": today_attendance,

        "today_production": today_production,

        "total_salary": total_salary,

    }

    return render(
        request,
        "hrms/dashboard.html",
        context,
    )


# =====================================================
# Department
# =====================================================

@login_required
def department_list(request):

    departments = Department.objects.all()

    return render(
        request,
        "hrms/department_list.html",
        {
            "departments": departments
        }
    )


@login_required
def department_add(request):

    if request.method == "POST":

        form = DepartmentForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Department Added Successfully."
            )

            return redirect("department_list")

    else:

        form = DepartmentForm()

    return render(
        request,
        "hrms/department_form.html",
        {
            "form": form
        }
    )


@login_required
def department_edit(request, pk):

    department = get_object_or_404(
        Department,
        pk=pk
    )

    if request.method == "POST":

        form = DepartmentForm(
            request.POST,
            instance=department
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Department Updated."
            )

            return redirect(
                "department_list"
            )

    else:

        form = DepartmentForm(
            instance=department
        )

    return render(
        request,
        "hrms/department_form.html",
        {
            "form": form
        }
    )


@login_required
def department_delete(request, pk):

    department = get_object_or_404(
        Department,
        pk=pk
    )

    department.delete()

    messages.success(
        request,
        "Department Deleted."
    )

    return redirect(
        "department_list"
    )


# =====================================================
# Employee List
# =====================================================

@login_required
def employee_list(request):

    search = request.GET.get(
        "search",
        ""
    )

    department = request.GET.get(
        "department",
        ""
    )

    employees = Employee.objects.all()

    if search:

        employees = employees.filter(
            name__icontains=search
        )

    if department:

        employees = employees.filter(
            department_id=department
        )

    context = {

        "employees": employees,

        "departments": Department.objects.all(),

        "search": search,

        "department": department,

    }

    return render(
        request,
        "hrms/employee_list.html",
        context,
    )


# =====================================================
# Employee Add
# =====================================================

@login_required
def employee_add(request):

    if request.method == "POST":

        form = EmployeeForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Employee Added Successfully."
            )

            return redirect(
                "employee_list"
            )

    else:

        form = EmployeeForm()

    return render(
        request,
        "hrms/employee_form.html",
        {
            "form": form
        }
    )


# =====================================================
# Employee Edit
# =====================================================

@login_required
def employee_edit(request, pk):

    employee = get_object_or_404(
        Employee,
        pk=pk
    )

    if request.method == "POST":

        form = EmployeeForm(
            request.POST,
            request.FILES,
            instance=employee
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Employee Updated."
            )

            return redirect(
                "employee_list"
            )

    else:

        form = EmployeeForm(
            instance=employee
        )

    return render(
        request,
        "hrms/employee_form.html",
        {
            "form": form
        }
    )


# =====================================================
# Employee Delete
# =====================================================

@login_required
def employee_delete(request, pk):

    employee = get_object_or_404(
        Employee,
        pk=pk
    )

    employee.delete()

    messages.success(
        request,
        "Employee Deleted Successfully."
    )

    return redirect(
        "employee_list"
    )


# =====================================================
# Employee Details
# =====================================================

@login_required
def employee_detail(request, pk):

    employee = get_object_or_404(
        Employee,
        pk=pk
    )

    attendance = Attendance.objects.filter(
        employee=employee
    ).order_by("-date")[:20]

    production = Production.objects.filter(
        employee=employee
    ).order_by("-date")[:20]

    salary = Salary.objects.filter(
        employee=employee
    ).order_by("-year", "-month")

    total_production = (
        Production.objects.filter(
            employee=employee
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0
    )

    total_ot = (
        Attendance.objects.filter(
            employee=employee
        ).aggregate(
            total=Sum("overtime_hours")
        )["total"] or Decimal("0")
    )

    context = {

        "employee": employee,

        "attendance": attendance,

        "production": production,

        "salary": salary,

        "total_production": total_production,

        "total_ot": total_ot,

    }

    return render(
        request,
        "hrms/employee_detail.html",
        context,
    )
    
from datetime import datetime
from decimal import Decimal


# =====================================================
# Attendance List
# =====================================================

@login_required
def attendance_list(request):

    search = request.GET.get("search", "")
    date = request.GET.get("date", "")

    attendance = Attendance.objects.select_related("employee")

    if search:
        attendance = attendance.filter(
            employee__name__icontains=search
        )

    if date:
        attendance = attendance.filter(date=date)

    attendance = attendance.order_by("-date")

    return render(
        request,
        "hrms/attendance_list.html",
        {
            "attendance": attendance,
            "search": search,
            "date": date,
        },
    )


# =====================================================
# Attendance Add
# =====================================================
@login_required
def attendance_add(request):

    if request.method == "POST":

        form = AttendanceForm(request.POST)

        if form.is_valid():

            attendance = form.save(commit=False)

            attendance.created_by = request.user

            if attendance.in_time and attendance.out_time:

                start = datetime.combine(
                    attendance.date,
                    attendance.in_time,
                )

                end = datetime.combine(
                    attendance.date,
                    attendance.out_time,
                )

                if end <= start:

                    form.add_error(
                        "out_time",
                        "Out Time must be greater than In Time."
                    )

                    return render(
                        request,
                        "hrms/attendance_form.html",
                        {
                            "form": form
                        },
                    )

                hours = Decimal(
                    (end - start).total_seconds() / 3600
                )

                attendance.working_hours = round(hours, 2)

                if hours > Decimal("8"):

                    attendance.overtime_hours = round(
                        hours - Decimal("8"),
                        2,
                    )

                else:

                    attendance.overtime_hours = Decimal("0")

            else:

                attendance.working_hours = Decimal("0")
                attendance.overtime_hours = Decimal("0")

            attendance.save()

            messages.success(
                request,
                "Attendance Saved Successfully."
            )

            return redirect("attendance_list")

    else:

        form = AttendanceForm()

    return render(
        request,
        "hrms/attendance_form.html",
        {
            "form": form
        },
    )
# =====================================================
# Attendance Edit
# =====================================================

@login_required
def attendance_edit(request, pk):

    attendance = get_object_or_404(
        Attendance,
        pk=pk,
    )

    if request.method == "POST":

        form = AttendanceForm(
            request.POST,
            instance=attendance,
        )

        if form.is_valid():

            attendance = form.save(commit=False)

            if attendance.in_time and attendance.out_time:

                start = datetime.combine(
                    attendance.date,
                    attendance.in_time,
                )

                end = datetime.combine(
                    attendance.date,
                    attendance.out_time,
                )

                hours = Decimal(
                    (end - start).total_seconds() / 3600
                )

                attendance.working_hours = round(hours, 2)

                if hours > 8:

                    attendance.overtime_hours = round(
                        hours - Decimal("8"),
                        2,
                    )

                else:

                    attendance.overtime_hours = Decimal("0")

            attendance.save()

            messages.success(
                request,
                "Attendance Updated."
            )

            return redirect("attendance_list")

    else:

        form = AttendanceForm(
            instance=attendance
        )

    return render(
        request,
        "hrms/attendance_form.html",
        {
            "form": form
        },
    )


# =====================================================
# Attendance Delete
# =====================================================

@login_required
def attendance_delete(request, pk):

    attendance = get_object_or_404(
        Attendance,
        pk=pk,
    )

    attendance.delete()

    messages.success(
        request,
        "Attendance Deleted."
    )

    return redirect("attendance_list")


# =====================================================
# Production List
# =====================================================

@login_required
def production_list(request):

    search = request.GET.get("search", "")

    production = Production.objects.select_related(
        "employee"
    )

    if search:

        production = production.filter(
            employee__name__icontains=search
        )

    production = production.order_by("-date")

    total_qty = (
        production.aggregate(
            qty=Sum("quantity")
        )["qty"] or 0
    )

    total_amount = (
        production.aggregate(
            amt=Sum("total_amount")
        )["amt"] or 0
    )

    return render(
        request,
        "hrms/production_list.html",
        {
            "production": production,
            "total_qty": total_qty,
            "total_amount": total_amount,
            "search": search,
        },
    )


# =====================================================
# Production Add
# =====================================================

@login_required
def production_add(request):

    if request.method == "POST":

        form = ProductionForm(request.POST)

        if form.is_valid():

            production = form.save(commit=False)

            production.created_by = request.user

            production.total_amount = (
                Decimal(production.quantity)
                * Decimal(production.rate)
            )

            production.save()

            messages.success(
                request,
                "Production Saved."
            )

            return redirect("production_list")

    else:

        form = ProductionForm()

    return render(
        request,
        "hrms/production_form.html",
        {
            "form": form
        },
    )


# =====================================================
# Production Edit
# =====================================================

@login_required
def production_edit(request, pk):

    production = get_object_or_404(
        Production,
        pk=pk,
    )

    if request.method == "POST":

        form = ProductionForm(
            request.POST,
            instance=production,
        )

        if form.is_valid():

            production = form.save(commit=False)

            production.total_amount = (
                Decimal(production.quantity)
                * Decimal(production.rate)
            )

            production.save()

            messages.success(
                request,
                "Production Updated."
            )

            return redirect("production_list")

    else:

        form = ProductionForm(
            instance=production
        )

    return render(
        request,
        "hrms/production_form.html",
        {
            "form": form
        },
    )


# =====================================================
# Production Delete
# =====================================================

@login_required
def production_delete(request, pk):

    production = get_object_or_404(
        Production,
        pk=pk,
    )

    production.delete()

    messages.success(
        request,
        "Production Deleted."
    )

    return redirect("production_list")


from calendar import monthrange
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# =====================================================
# Generate Salary
# =====================================================

@login_required
def generate_salary(request):

    if request.method == "POST":

        employee_id = request.POST.get("employee")

        month = int(request.POST.get("month"))

        year = int(request.POST.get("year"))

        employee = get_object_or_404(
            Employee,
            pk=employee_id
        )

        attendance = Attendance.objects.filter(
            employee=employee,
            date__month=month,
            date__year=year
        )

        production = Production.objects.filter(
            employee=employee,
            date__month=month,
            date__year=year
        )

        advance = (
            Advance.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0")
        )

        bonus = (
            Bonus.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0")
        )

        deduction = (
            Deduction.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0")
        )

        overtime = (
            attendance.aggregate(
                total=Sum("overtime_hours")
            )["total"] or Decimal("0")
        )

        production_amount = (
            production.aggregate(
                total=Sum("total_amount")
            )["total"] or Decimal("0")
        )

        overtime_amount = (
            overtime *
            employee.overtime_rate
        )

        pf_amount = (
            employee.basic_salary *
            employee.pf_percent
        ) / 100

        esi_amount = (
            employee.basic_salary *
            employee.esi_percent
        ) / 100

        net_salary = (

            employee.basic_salary

            + overtime_amount

            + production_amount

            + bonus

            - advance

            - deduction

            - pf_amount

            - esi_amount

        )

        Salary.objects.update_or_create(

            employee=employee,

            month=month,

            year=year,

            defaults={

                "basic_salary": employee.basic_salary,

                "overtime_amount": overtime_amount,

                "production_amount": production_amount,

                "bonus": bonus,

                "advance": advance,

                "deduction": deduction,

                "pf_amount": pf_amount,

                "esi_amount": esi_amount,

                "net_salary": net_salary,

            }

        )

        messages.success(
            request,
            "Salary Generated Successfully."
        )

        return redirect(
            "salary_list"
        )

    return render(
        request,
        "hrms/generate_salary.html",
        {
            "employees": Employee.objects.filter(
                status="Active"
            )
        }
    )


# =====================================================
# Salary List
# =====================================================

@login_required
def salary_list(request):

    salaries = Salary.objects.select_related(
        "employee"
    ).order_by(
        "-year",
        "-month"
    )

    return render(
        request,
        "hrms/salary_list.html",
        {
            "salaries": salaries
        }
    )


# =====================================================
# Salary Slip
# =====================================================

@login_required
def salary_slip(request, pk):

    salary = get_object_or_404(
        Salary,
        pk=pk
    )

    return render(
        request,
        "hrms/salary_slip.html",
        {
            "salary": salary
        }
    )


# =====================================================
# Advance CRUD
# =====================================================

@login_required
def advance_list(request):

    advances = Advance.objects.select_related(
        "employee"
    ).order_by("-date")

    return render(
        request,
        "hrms/advance_list.html",
        {
            "advances": advances
        }
    )


@login_required
def advance_add(request):

    if request.method == "POST":

        form = AdvanceForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Advance Saved."
            )

            return redirect(
                "advance_list"
            )

    else:

        form = AdvanceForm()

    return render(
        request,
        "hrms/advance_form.html",
        {
            "form": form
        }
    )


# =====================================================
# Bonus CRUD
# =====================================================

@login_required
def bonus_list(request):

    bonus = Bonus.objects.select_related(
        "employee"
    ).order_by("-date")

    return render(
        request,
        "hrms/bonus_list.html",
        {
            "bonus": bonus
        }
    )


@login_required
def bonus_add(request):

    if request.method == "POST":

        form = BonusForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Bonus Saved."
            )

            return redirect(
                "bonus_list"
            )

    else:

        form = BonusForm()

    return render(
        request,
        "hrms/bonus_form.html",
        {
            "form": form
        }
    )


# =====================================================
# Deduction CRUD
# =====================================================

@login_required
def deduction_list(request):

    deductions = Deduction.objects.select_related(
        "employee"
    ).order_by("-date")

    return render(
        request,
        "hrms/deduction_list.html",
        {
            "deductions": deductions
        }
    )


@login_required
def deduction_add(request):

    if request.method == "POST":

        form = DeductionForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Deduction Saved."
            )

            return redirect(
                "deduction_list"
            )

    else:

        form = DeductionForm()

    return render(
        request,
        "hrms/deduction_form.html",
        {
            "form": form
        }
    )


# =====================================================
# Employee Monthly Summary
# =====================================================

@login_required
def employee_month_summary(
    request,
    employee_id,
    month,
    year
):

    employee = get_object_or_404(
        Employee,
        pk=employee_id
    )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__month=month,
        date__year=year
    )

    production = Production.objects.filter(
        employee=employee,
        date__month=month,
        date__year=year
    )

    salary = Salary.objects.filter(
        employee=employee,
        month=month,
        year=year
    ).first()

    context = {

        "employee": employee,

        "attendance": attendance,

        "production": production,

        "salary": salary,

        "present_days": attendance.filter(
            status="Present"
        ).count(),

        "absent_days": attendance.filter(
            status="Absent"
        ).count(),

        "holiday_days": attendance.filter(
            status="Holiday"
        ).count(),

        "week_off": attendance.filter(
            status="Week Off"
        ).count(),

        "total_ot": attendance.aggregate(
            total=Sum(
                "overtime_hours"
            )
        )["total"] or 0,

        "total_qty": production.aggregate(
            total=Sum(
                "quantity"
            )
        )["total"] or 0,

        "total_amount": production.aggregate(
            total=Sum(
                "total_amount"
            )
        )["total"] or 0,

    }

    return render(
        request,
        "hrms/month_summary.html",
        context
    )