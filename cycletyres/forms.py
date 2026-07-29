from django import forms
from .models import CycleTyreItem, BUCKET_CHOICES

INPUT_CLS = "w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-600"


class CycleTyreItemForm(forms.ModelForm):
    class Meta:
        model = CycleTyreItem
        fields = ["box_type", "size", "material", "brand", "weight"]
        widgets = {
            "box_type": forms.TextInput(attrs={"placeholder": "e.g. 6 ply", "class": INPUT_CLS}),
            "size": forms.TextInput(attrs={"placeholder": "e.g. 28 x 1.5", "class": INPUT_CLS}),
            "material": forms.TextInput(attrs={"placeholder": "e.g. CTC / NYL", "class": INPUT_CLS}),
            "brand": forms.TextInput(attrs={"placeholder": "e.g. SUPER", "class": INPUT_CLS}),
            "weight": forms.NumberInput(attrs={"placeholder": "Weight in Kg (e.g. 0.750)", "step": "0.001", "class": INPUT_CLS}),
        }


class ProductionEntryForm(forms.Form):
    tyre_item = forms.ModelChoiceField(
        queryset=CycleTyreItem.objects.filter(is_active=True), label="Cycle Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    
    all_curing = forms.IntegerField(min_value=1, label="All Curing (Total Qty)",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS, "id": "id_all_curing", "placeholder": "Total Curing Qty"}))
    second_grade = forms.IntegerField(min_value=0, initial=0, label="2nd Grade Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS, "id": "id_second_grade", "placeholder": "2nd Grade Qty"}))
    rejected_grade = forms.IntegerField(min_value=0, initial=0, label="Rejected Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS, "id": "id_rejected_grade", "placeholder": "Rejected Qty"}))
    first_grade = forms.IntegerField(min_value=0, initial=0, label="1st Grade / Black (Calculated)",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS, "id": "id_first_grade", "readonly": "readonly", "style": "background-color: #f1f5f9; font-weight: bold;"}))
    
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Remark (optional)", "class": INPUT_CLS}))


class SaleEntryForm(forms.Form):
    tyre_item = forms.ModelChoiceField(
        queryset=CycleTyreItem.objects.filter(is_active=True), label="Cycle Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    bucket = forms.ChoiceField(choices=BUCKET_CHOICES, label="Sale From",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Sale Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    bill_number = forms.CharField(required=True, label="Bill Number",
        widget=forms.TextInput(attrs={"placeholder": "e.g. INV-1023", "class": INPUT_CLS}))
    remark = forms.CharField(required=False, label="Remark",
        widget=forms.TextInput(attrs={"placeholder": "Party name, notes waghera (optional)", "class": INPUT_CLS}))


class AdjustmentEntryForm(forms.Form):
    ACTION_CHOICES = [("add", "Add (+)"), ("subtract", "Subtract (-)")]
    tyre_item = forms.ModelChoiceField(
        queryset=CycleTyreItem.objects.filter(is_active=True), label="Cycle Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    bucket = forms.ChoiceField(choices=BUCKET_CHOICES, label="Bucket",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    action = forms.ChoiceField(choices=ACTION_CHOICES, label="Action",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Quantity",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Reason / remark (e.g. R.F.M. return)", "class": INPUT_CLS}))


class CycleTyreDailyManualEntryForm(forms.ModelForm):
    class Meta:
        from .models import CycleTyreDailyManualEntry
        model = CycleTyreDailyManualEntry
        fields = ["date", "parchi_kg", "mixing_actual_compound", "chakka", "calander_bias_cutt", "packing_wastage", "tar"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}),
            "parchi_kg": forms.NumberInput(attrs={"class": INPUT_CLS, "step": "0.01", "placeholder": "Packing Parch Kg"}),
            "mixing_actual_compound": forms.NumberInput(attrs={"class": INPUT_CLS, "step": "0.01", "placeholder": "Mixing Actual Compound"}),
            "chakka": forms.NumberInput(attrs={"class": INPUT_CLS, "step": "0.01", "placeholder": "Chakka"}),
            "calander_bias_cutt": forms.NumberInput(attrs={"class": INPUT_CLS, "step": "0.01", "placeholder": "Calander Bias Cutt."}),
            "packing_wastage": forms.NumberInput(attrs={"class": INPUT_CLS, "step": "0.01", "placeholder": "Packing Wastage"}),
            "tar": forms.NumberInput(attrs={"class": INPUT_CLS, "step": "0.01", "placeholder": "Tar"}),
        }