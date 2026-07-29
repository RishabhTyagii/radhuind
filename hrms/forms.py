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
            "name": forms.TextInput(attrs={
                "class": "form-control"
            }),
        }


# ===========================
# Employee
# ===========================

class EmployeeForm(forms.ModelForm):

    class Meta:
        model = Employee

        fields = "__all__"

        widgets = {

            "employee_code": forms.TextInput(attrs={"class":"form-control"}),

            "name": forms.TextInput(attrs={"class":"form-control"}),

            "father_name": forms.TextInput(attrs={"class":"form-control"}),

            "mobile": forms.TextInput(attrs={"class":"form-control"}),

            "alternate_mobile": forms.TextInput(attrs={"class":"form-control"}),

            "email": forms.EmailInput(attrs={"class":"form-control"}),

            "dob": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "joining_date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "department": forms.Select(attrs={"class":"form-select"}),

            "designation": forms.TextInput(attrs={"class":"form-control"}),

            "employee_type": forms.Select(attrs={"class":"form-select"}),

            "contractor_name": forms.TextInput(attrs={"class":"form-control"}),

            "address": forms.Textarea(
                attrs={
                    "class":"form-control",
                    "rows":3
                }
            ),

            "aadhaar": forms.TextInput(attrs={"class":"form-control"}),

            "pan": forms.TextInput(attrs={"class":"form-control"}),

            "bank_name": forms.TextInput(attrs={"class":"form-control"}),

            "account_number": forms.TextInput(attrs={"class":"form-control"}),

            "ifsc": forms.TextInput(attrs={"class":"form-control"}),

            "uan": forms.TextInput(attrs={"class":"form-control"}),

            "esi_number": forms.TextInput(attrs={"class":"form-control"}),

            "basic_salary": forms.NumberInput(attrs={"class":"form-control"}),

            "hourly_rate": forms.NumberInput(attrs={"class":"form-control"}),

            "overtime_rate": forms.NumberInput(attrs={"class":"form-control"}),

            "pf_percent": forms.NumberInput(attrs={"class":"form-control"}),

            "esi_percent": forms.NumberInput(attrs={"class":"form-control"}),

            "status": forms.Select(attrs={"class":"form-select"}),

            "photo": forms.ClearableFileInput(
                attrs={
                    "class":"form-control"
                }
            ),

        }


# ===========================
# Attendance
# ===========================

class AttendanceForm(forms.ModelForm):

    class Meta:

        model = Attendance

        fields = [
            "employee",
            "date",
            "in_time",
            "out_time",
            "status",
            "leave_type",
            "remarks",
        ]

        widgets = {

            "employee": forms.Select(
                attrs={"class":"form-select"}
            ),

            "date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "in_time": forms.TimeInput(
                attrs={
                    "type":"time",
                    "class":"form-control"
                }
            ),

            "out_time": forms.TimeInput(
                attrs={
                    "type":"time",
                    "class":"form-control"
                }
            ),

            "status": forms.Select(
                attrs={"class":"form-select"}
            ),

            "leave_type": forms.Select(
                attrs={"class":"form-select"}
            ),

            "remarks": forms.Textarea(
                attrs={
                    "rows":3,
                    "class":"form-control"
                }
            ),

            "created_by": forms.Select(
                attrs={"class":"form-select"}
            ),

        }


# ===========================
# Production
# ===========================

class ProductionForm(forms.ModelForm):

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

            "employee": forms.Select(
                attrs={"class":"form-select"}
            ),

            "date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "product_name": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "rate": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "rows":3,
                    "class":"form-control"
                }
            ),

            "created_by": forms.Select(
                attrs={"class":"form-select"}
            ),

        }


# ===========================
# Advance
# ===========================

class AdvanceForm(forms.ModelForm):

    class Meta:

        model = Advance

        fields = "__all__"

        widgets = {

            "employee": forms.Select(attrs={"class":"form-select"}),

            "date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "rows":3,
                    "class":"form-control"
                }
            ),

        }


# ===========================
# Bonus
# ===========================

class BonusForm(forms.ModelForm):

    class Meta:

        model = Bonus

        fields = "__all__"

        widgets = {

            "employee": forms.Select(attrs={"class":"form-select"}),

            "date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "rows":3,
                    "class":"form-control"
                }
            ),

        }


# ===========================
# Deduction
# ===========================

class DeductionForm(forms.ModelForm):

    class Meta:

        model = Deduction

        fields = "__all__"

        widgets = {

            "employee": forms.Select(attrs={"class":"form-select"}),

            "date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "rows":3,
                    "class":"form-control"
                }
            ),

        }