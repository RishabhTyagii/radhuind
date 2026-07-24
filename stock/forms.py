from django import forms
from .models import TyreItem, DailyEntry, BUCKET_CHOICES

INPUT_CLS = "w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-600"

class TyreItemForm(forms.ModelForm):
    class Meta:
        model = TyreItem
        fields = ["tyre", "pattern", "type", "weight"]
        widgets = {
            "tyre": forms.TextInput(attrs={"placeholder": "e.g. 275-18", "class": INPUT_CLS}),
            "pattern": forms.TextInput(attrs={"placeholder": "e.g. PANTHER", "class": INPUT_CLS}),
            "type": forms.TextInput(attrs={"placeholder": "e.g. TT / TL", "class": INPUT_CLS}),
            "weight": forms.NumberInput(attrs={"placeholder": "e.g. 8.5", "step": "0.01", "class": INPUT_CLS}),
        }

class ProductionEntryForm(forms.Form):
    tyre_item = forms.ModelChoiceField(
        queryset=TyreItem.objects.filter(is_active=True), label="Tyre",
        widget=forms.Select(attrs={"class": INPUT_CLS}))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLS}))
    all_curing = forms.IntegerField(min_value=0, label="All Curing",
        widget=forms.NumberInput(attrs={"class": INPUT_CLS, "placeholder": "Aaj total kitna bana"}))
    production_tyre = forms.IntegerField(min_value=0, label="Production Tyre", initial=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLS, "placeholder": "Pichla/beech wala jo aaj complete hua"}))
    repair = forms.IntegerField(min_value=0, label="Repair", initial=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    second_grade = forms.IntegerField(min_value=0, label="2nd Grade", initial=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    third_grade = forms.IntegerField(min_value=0, label="3rd Grade", initial=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    lose_tyre = forms.IntegerField(min_value=0, label="Lose Tyre", initial=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLS}))
    actual_weight = forms.DecimalField(required=False, min_value=0, label="Actual Weight (KG) - optional",
        widget=forms.NumberInput(attrs={"placeholder": "Is batch ka tola hua weight (optional)", "step": "0.01", "class": INPUT_CLS}))
    remark = forms.CharField(required=False,
        widget=forms.TextInput(attrs={"placeholder": "Remark (optional)", "class": INPUT_CLS}))

    def clean(self):
        cleaned = super().clean()
        all_curing = cleaned.get("all_curing") or 0
        production_tyre = cleaned.get("production_tyre") or 0
        repair = cleaned.get("repair") or 0
        second_grade = cleaned.get("second_grade") or 0
        third_grade = cleaned.get("third_grade") or 0
        lose_tyre = cleaned.get("lose_tyre") or 0

        packing = (all_curing + production_tyre) - (repair + second_grade + third_grade + lose_tyre)
        if packing < 0:
            raise forms.ValidationError(
                f"Numbers galat lag rahe hain — Packing negative aa raha hai ({packing}). "
                f"All Curing + Production Tyre, Repair/2nd/3rd/Lose Tyre se kam nahi ho sakta."
            )
        cleaned["packing"] = packing
        return cleaned
    
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
