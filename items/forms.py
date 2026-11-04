from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report

       
        fields = [
            "item_type",
            "title",
            "category",
            "happened_on",
            "location",
            "location_details",
            "description",
            "image",
        ]


        widgets = {
            "happened_on": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }