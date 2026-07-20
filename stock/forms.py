from django import forms
from .models import TyreItem, DailyEntry, BUCKET_CHOICES

INPUT_CLS = "w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-600"


class TyreItemForm(forms.ModelForm):
    class Meta:
        model = TyreItem
        fields = ["tyre", "pattern", "type"]
        widgets = {
            "tyre": forms.TextInput(attrs={"placeholder": "e.g. 275-18", "class": INPUT_CLS}),
            "pattern": forms.TextInput(attrs={"placeholder": "e.g. PANTHER", "class": INPUT_CLS}),
            "type": forms.TextInput(attrs={"placeholder": "e.g. TT / TL", "class": INPUT_CLS}),
        }


class ProductionEntryForm(forms.Form):
    tyre_item = forms.ModelChoiceField(
        queryset=TyreItem.objects.filter(is_active=True), label="Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Production Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Remark (optional)", "class": INPUT_CLS}))


class DispatchEntryForm(forms.Form):
    tyre_item = forms.ModelChoiceField(
        queryset=TyreItem.objects.filter(is_active=True), label="Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    bucket = forms.ChoiceField(choices=BUCKET_CHOICES, label="Dispatch From",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Dispatch Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    bill_number = forms.CharField(required=True, label="Bill Number",
        widget=forms.TextInput(attrs={"placeholder": "e.g. INV-1023", "class": INPUT_CLS}))
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Remark (optional)", "class": INPUT_CLS}))


class AdjustmentEntryForm(forms.Form):
    ACTION_CHOICES = [("add", "Add (+)"), ("subtract", "Subtract (-)")]
    tyre_item = forms.ModelChoiceField(
        queryset=TyreItem.objects.filter(is_active=True), label="Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    bucket = forms.ChoiceField(choices=BUCKET_CHOICES, label="Bucket",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    action = forms.ChoiceField(choices=ACTION_CHOICES, label="Action",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Quantity",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Reason / remark", "class": INPUT_CLS}))
