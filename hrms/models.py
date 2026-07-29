from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


# ===========================
# Department
# ===========================

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ===========================
# Employee
# ===========================

EMPLOYEE_TYPE = (
    ("Company", "Company"),
    ("Contractor", "Contractor"),
)

STATUS = (
    ("Active", "Active"),
    ("Inactive", "Inactive"),
)


class Employee(models.Model):

    employee_code = models.CharField(max_length=20, unique=True)

    photo = models.ImageField(upload_to="employees/", blank=True, null=True)

    name = models.CharField(max_length=150)

    father_name = models.CharField(max_length=150, blank=True)

    mobile = models.CharField(max_length=15)

    alternate_mobile = models.CharField(max_length=15, blank=True)

    email = models.EmailField(blank=True)

    dob = models.DateField(null=True,blank=True)

    joining_date = models.DateField(null=True,blank=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    designation = models.CharField(max_length=100)

    employee_type = models.CharField(
        max_length=20,
        choices=EMPLOYEE_TYPE,
        default="Company"
    )

    contractor_name = models.CharField(
        max_length=150,
        blank=True
    )

    address = models.TextField(blank=True)

    aadhaar = models.CharField(
        max_length=12,
        blank=True
    )

    pan = models.CharField(
        max_length=10,
        blank=True
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True
    )

    account_number = models.CharField(
        max_length=50,
        blank=True
    )

    ifsc = models.CharField(
        max_length=20,
        blank=True
    )

    uan = models.CharField(
        max_length=30,
        blank=True
    )

    esi_number = models.CharField(
        max_length=30,
        blank=True
    )

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    overtime_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    pf_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    esi_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default="Active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_code} - {self.name}"


# ===========================
# Leave Balance
# ===========================

class LeaveBalance(models.Model):

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE
    )

    year = models.IntegerField()

    cl_balance = models.IntegerField(default=7)

    el_balance = models.IntegerField(default=13)

    def __str__(self):
        return self.employee.name


# ===========================
# Attendance
# ===========================

ATTENDANCE_STATUS = (
    ("Present", "Present"),
    ("Absent", "Absent"),
    ("Half Day", "Half Day"),
    ("Holiday", "Holiday"),
    ("Week Off", "Week Off"),
)

LEAVE_TYPE = (
    ("", "---------"),
    ("CL", "CL"),
    ("EL", "EL"),
    ("LOP", "LOP"),
)


class Attendance(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    in_time = models.TimeField(
        blank=True,
        null=True
    )

    out_time = models.TimeField(
        blank=True,
        null=True
    )

    working_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS,
        default="Present"
    )

    leave_type = models.CharField(
        max_length=10,
        choices=LEAVE_TYPE,
        blank=True
    )

    remarks = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ("employee", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee.name} - {self.date}"


# ===========================
# Production
# ===========================

class Production(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    product_name = models.CharField(
        max_length=150
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    remarks = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity) * Decimal(self.rate)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee.name} - {self.product_name}"


# ===========================
# Advance
# ===========================

class Advance(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.employee.name


# ===========================
# Bonus
# ===========================

class Bonus(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.employee.name


# ===========================
# Deduction
# ===========================

class Deduction(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.employee.name


# ===========================
# Salary
# ===========================

class Salary(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    month = models.IntegerField()

    year = models.IntegerField()

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    overtime_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    production_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    bonus = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    advance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    deduction = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    pf_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    esi_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    generated_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("employee", "month", "year")

    def __str__(self):
        return f"{self.employee.name} - {self.month}/{self.year}"