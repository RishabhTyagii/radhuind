from django import forms
from .models import CycleTyreItem, BUCKET_CHOICES

INPUT_CLS = "w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-600"


class CycleTyreItemForm(forms.ModelForm):
    class Meta:
        model = CycleTyreItem
        fields = ["box_type", "size", "material", "brand"]
        widgets = {
            "box_type": forms.TextInput(attrs={"placeholder": "e.g. 6 ply", "class": INPUT_CLS}),
            "size": forms.TextInput(attrs={"placeholder": "e.g. 28 x 1.5", "class": INPUT_CLS}),
            "material": forms.TextInput(attrs={"placeholder": "e.g. CTC / NYL", "class": INPUT_CLS}),
            "brand": forms.TextInput(attrs={"placeholder": "e.g. SUPER", "class": INPUT_CLS}),
        }


class ProductionEntryForm(forms.Form):
    tyre_item = forms.ModelChoiceField(
        queryset=CycleTyreItem.objects.filter(is_active=True), label="Cycle Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    quantity = forms.IntegerField(min_value=1, label="Production Qty",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
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