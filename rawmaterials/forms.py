from django import forms
from .models import StockEntry, Material


class StockEntryForm(forms.ModelForm):

    material = forms.ModelChoiceField(
        queryset=Material.objects.select_related("group").all(),
        empty_label="Search Material..."
    )

    class Meta:
        model = StockEntry

        fields = [
            "date",
            "material",
            "received_quantity",
            "received_by",
            "used_quantity",
        ]

        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full border rounded p-2"
                }
            ),

            "received_quantity": forms.NumberInput(
                attrs={
                    "class": "w-full border rounded p-2"
                }
            ),

            "received_by": forms.TextInput(
                attrs={
                    "class": "w-full border rounded p-2"
                }
            ),

            "used_quantity": forms.NumberInput(
                attrs={
                    "class": "w-full border rounded p-2"
                }
            ),
        }
        
class TallyFilterForm(forms.Form):

    material = forms.ModelChoiceField(
        queryset=Material.objects.select_related("group").all(),
        required=False,
        empty_label="Select Material",
        widget=forms.Select(attrs={
            "class": "w-full border rounded p-2"
        })
    )

    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full border rounded p-2"
        })
    )

    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full border rounded p-2"
        })
    )