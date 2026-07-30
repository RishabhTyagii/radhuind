from django import forms
from .models import CycleTubeItem, CycleTubeDailyManualEntry, BUCKET_CHOICES, TUBE_QUALITY_CHOICES

INPUT_CLS = "w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-600"
NUM_CLS   = "w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"


class CycleTubeItemForm(forms.ModelForm):
    class Meta:
        model = CycleTubeItem
        fields = ["size", "type", "brand", "weight"]
        widgets = {
            "size":   forms.TextInput(attrs={"placeholder": "e.g. 28x1.5", "class": INPUT_CLS}),
            "type":   forms.TextInput(attrs={"placeholder": "e.g. JT / MLD", "class": INPUT_CLS}),
            "brand":  forms.TextInput(attrs={"placeholder": "e.g. TAHALKA", "class": INPUT_CLS}),
            "weight": forms.NumberInput(attrs={
                "placeholder": "e.g. 0.2809",
                "class": INPUT_CLS,
                "step": "0.0001",
                "min": "0",
            }),
        }


class ProductionEntryForm(forms.Form):
    tube_item = forms.ModelChoiceField(
        queryset=CycleTubeItem.objects.filter(is_active=True), label="Cycle Tube",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Production Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    tube_quality = forms.ChoiceField(
        choices=TUBE_QUALITY_CHOICES, label="Tube Quality",
        widget=forms.RadioSelect(attrs={"class": "mr-1"}),
        initial="normal",
    )
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Remark (optional)", "class": INPUT_CLS}))


class SaleEntryForm(forms.Form):
    tube_item = forms.ModelChoiceField(
        queryset=CycleTubeItem.objects.filter(is_active=True), label="Cycle Tube",
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
    tube_item = forms.ModelChoiceField(
        queryset=CycleTubeItem.objects.filter(is_active=True), label="Cycle Tube",
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


class CycleTubeDailyManualEntryForm(forms.ModelForm):
    """Form for the daily manual entry panel in the production summary."""
    class Meta:
        model = CycleTubeDailyManualEntry
        fields = [
            "date",
            "valve_body_issued",
            "actual_wt_gross",
            "actual_mixing_compound",
            "jali",
            "die_wastage",
            "tube_cutting",
            "total_tube_waste",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": NUM_CLS}),
            "valve_body_issued":       forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
            "actual_wt_gross":         forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
            "actual_mixing_compound":  forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
            "jali":                    forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
            "die_wastage":             forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
            "tube_cutting":            forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
            "total_tube_waste":        forms.NumberInput(attrs={"class": NUM_CLS, "step": "0.01"}),
        }
        labels = {
            "valve_body_issued":      "Valve Body Issued",
            "actual_wt_gross":        "Actual wt kgs (Gross)",
            "actual_mixing_compound": "Actual Mixing Compound (kgs)",
            "jali":                   "Jali (kgs)",
            "die_wastage":            "Die Wastage (kgs)",
            "tube_cutting":           "Tube Cutting (kgs)",
            "total_tube_waste":       "Total Tube Waste (kgs)",
        }