from django.contrib import admin

from .models import (
    Department,
    Employee,
    LeaveBalance,
    Attendance,
    Production,
    Advance,
    Bonus,
    Deduction,
    Salary,
)


# ===========================
# Department
# ===========================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )


# ===========================
# Employee
# ===========================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = (
        "employee_code",
        "name",
        "department",
        "designation",
        "employee_type",
        "mobile",
        "basic_salary",
        "status",
    )

    search_fields = (
        "employee_code",
        "name",
        "mobile",
        "aadhaar",
        "pan",
    )

    list_filter = (
        "department",
        "employee_type",
        "status",
    )

    ordering = (
        "employee_code",
    )

    readonly_fields = (
        "created_at",
    )


# ===========================
# Leave Balance
# ===========================

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "year",
        "cl_balance",
        "el_balance",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
    )

    list_filter = (
        "year",
    )


# ===========================
# Attendance
# ===========================

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "date",
        "status",
        "working_hours",
        "overtime_hours",
        "leave_type",
        "created_by",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
    )

    list_filter = (
        "date",
        "status",
        "leave_type",
    )

    date_hierarchy = "date"

    ordering = (
        "-date",
    )


# ===========================
# Production
# ===========================

@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "date",
        "product_name",
        "quantity",
        "rate",
        "total_amount",
        "created_by",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
        "product_name",
    )

    list_filter = (
        "date",
    )

    date_hierarchy = "date"

    ordering = (
        "-date",
    )

    readonly_fields = (
        "total_amount",
        "created_at",
    )


# ===========================
# Advance
# ===========================

@admin.register(Advance)
class AdvanceAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "date",
        "amount",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
    )

    list_filter = (
        "date",
    )

    ordering = (
        "-date",
    )


# ===========================
# Bonus
# ===========================

@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "date",
        "amount",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
    )

    list_filter = (
        "date",
    )

    ordering = (
        "-date",
    )


# ===========================
# Deduction
# ===========================

@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "date",
        "amount",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
    )

    list_filter = (
        "date",
    )

    ordering = (
        "-date",
    )


# ===========================
# Salary
# ===========================

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "month",
        "year",
        "basic_salary",
        "production_amount",
        "overtime_amount",
        "pf_amount",
        "esi_amount",
        "net_salary",
    )

    search_fields = (
        "employee__name",
        "employee__employee_code",
    )

    list_filter = (
        "month",
        "year",
    )

    ordering = (
        "-year",
        "-month",
    )

    readonly_fields = (
        "generated_on",
    )