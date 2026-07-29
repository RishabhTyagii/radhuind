from django import forms
from .models import (
    Department,
    Employee,
    Attendance,
    Production,
    Advance,
    Bonus,
    Deduction,
)


# ===========================
# Department
# ===========================

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


# ===========================
# Employee
# ===========================

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = "__all__"
        widgets = {
            "employee_code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "father_name": forms.TextInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
            "alternate_mobile": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "dob": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "joining_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
            "employee_type": forms.Select(attrs={"class": "form-select"}),
            "contractor_name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "aadhaar": forms.TextInput(attrs={"class": "form-control"}),
            "pan": forms.TextInput(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "account_number": forms.TextInput(attrs={"class": "form-control"}),
            "ifsc": forms.TextInput(attrs={"class": "form-control"}),
            "uan": forms.TextInput(attrs={"class": "form-control"}),
            "esi_number": forms.TextInput(attrs={"class": "form-control"}),
            "basic_salary": forms.NumberInput(attrs={"class": "form-control"}),
            "hourly_rate": forms.NumberInput(attrs={"class": "form-control"}),
            "overtime_rate": forms.NumberInput(attrs={"class": "form-control"}),
            "pf_percent": forms.NumberInput(attrs={"class": "form-control"}),
            "esi_percent": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# Helper mixin to set active employees & nice choice labels
class ActiveEmployeeFormMixin:
    def setup_employee_queryset(self):
        if "employee" in self.fields:
            self.fields["employee"].queryset = Employee.objects.filter(status="Active").select_related("department").order_by("name")
            self.fields["employee"].label_from_instance = lambda obj: f"{obj.employee_code} - {obj.name} ({obj.department.name if obj.department else 'No Dept'})"


# ===========================
# Attendance
# ===========================

class AttendanceForm(ActiveEmployeeFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_employee_queryset()

    class Meta:
        model = Attendance
        fields = [
            "employee",
            "date",
            "working_hours",
            "in_time",
            "out_time",
            "status",
            "leave_type",
            "remarks",
        ]
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "working_hours": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Direct Total Hours e.g. 8.0 or 12.0", "step": "0.5"}),
            "in_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "out_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "remarks": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


# ===========================
# Production
# ===========================

class ProductionForm(ActiveEmployeeFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_employee_queryset()

    class Meta:
        model = Production
        fields = [
            "employee",
            "date",
            "product_name",
            "quantity",
            "rate",
            "remarks",
        ]
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "product_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Curing Tyre / Tube Batch"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Qty produced"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Rate per unit"}),
            "remarks": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


# ===========================
# Advance
# ===========================

class AdvanceForm(ActiveEmployeeFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_employee_queryset()

    class Meta:
        model = Advance
        fields = "__all__"
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


# ===========================
# Bonus
# ===========================

class BonusForm(ActiveEmployeeFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_employee_queryset()

    class Meta:
        model = Bonus
        fields = "__all__"
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


# ===========================
# Deduction
# ===========================

class DeductionForm(ActiveEmployeeFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_employee_queryset()

    class Meta:
        model = Deduction
        fields = "__all__"
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }