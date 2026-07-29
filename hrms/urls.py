from django.urls import path

from . import views

urlpatterns = [

    # ===================================================
    # Dashboard
    # ===================================================

    path(
        "",
        views.dashboard,
        name="hr_dashboard",
    ),

    # ===================================================
    # Department
    # ===================================================

    path(
        "departments/",
        views.department_list,
        name="department_list",
    ),

    path(
        "departments/add/",
        views.department_add,
        name="department_add",
    ),

    path(
        "departments/<int:pk>/edit/",
        views.department_edit,
        name="department_edit",
    ),

    path(
        "departments/<int:pk>/delete/",
        views.department_delete,
        name="department_delete",
    ),

    # ===================================================
    # Employee
    # ===================================================

    path(
        "employees/",
        views.employee_list,
        name="employee_list",
    ),

    path(
        "employees/add/",
        views.employee_add,
        name="employee_add",
    ),

    path(
        "employees/<int:pk>/",
        views.employee_detail,
        name="employee_detail",
    ),

    path(
        "employees/<int:pk>/edit/",
        views.employee_edit,
        name="employee_edit",
    ),

    path(
        "employees/<int:pk>/delete/",
        views.employee_delete,
        name="employee_delete",
    ),

    # ===================================================
    # Attendance
    # ===================================================

    path(
        "attendance/",
        views.attendance_list,
        name="attendance_list",
    ),

    path(
        "attendance/add/",
        views.attendance_add,
        name="attendance_add",
    ),

    path(
        "attendance/<int:pk>/edit/",
        views.attendance_edit,
        name="attendance_edit",
    ),

    path(
        "attendance/<int:pk>/delete/",
        views.attendance_delete,
        name="attendance_delete",
    ),

    # ===================================================
    # Production
    # ===================================================

    path(
        "production/",
        views.production_list,
        name="production_list",
    ),

    path(
        "production/add/",
        views.production_add,
        name="production_add",
    ),

    path(
        "production/<int:pk>/edit/",
        views.production_edit,
        name="production_edit",
    ),

    path(
        "production/<int:pk>/delete/",
        views.production_delete,
        name="production_delete",
    ),

    # ===================================================
    # Salary
    # ===================================================

    path(
        "salary/",
        views.salary_list,
        name="salary_list",
    ),

    path(
        "salary/generate/",
        views.generate_salary,
        name="generate_salary",
    ),

    path(
        "salary/<int:pk>/slip/",
        views.salary_slip,
        name="salary_slip",
    ),

    # ===================================================
    # Advance
    # ===================================================

    path(
        "advance/",
        views.advance_list,
        name="advance_list",
    ),

    path(
        "advance/add/",
        views.advance_add,
        name="advance_add",
    ),

    # ===================================================
    # Bonus
    # ===================================================

    path(
        "bonus/",
        views.bonus_list,
        name="bonus_list",
    ),

    path(
        "bonus/add/",
        views.bonus_add,
        name="bonus_add",
    ),

    # ===================================================
    # Deduction
    # ===================================================

    path(
        "deduction/",
        views.deduction_list,
        name="deduction_list",
    ),

    path(
        "deduction/add/",
        views.deduction_add,
        name="deduction_add",
    ),

    # ===================================================
    # Monthly Summary
    # ===================================================

    path(
        "employee/<int:employee_id>/<int:month>/<int:year>/summary/",
        views.employee_month_summary,
        name="employee_month_summary",
    ),

]