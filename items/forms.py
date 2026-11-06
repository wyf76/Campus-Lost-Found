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
            "happened_time",
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
            "happened_time": forms.TimeInput(attrs={"type": "time"}),
        }

class ReportSearchForm(forms.Form):
    q = forms.CharField(required=False)
    type = forms.ChoiceField(choices=Report.ItemType.choices, required=False)
    category = forms.ChoiceField(choices=Report.Category.choices, required=False)
    location = forms.ChoiceField(choices=Report.Location.choices, required=False)
    date_from = forms.DateField(input_formats=["%Y-%m-%d"], required=False)
    date_to = forms.DateField(input_formats=["%Y-%m-%d"], required=False)
    status = forms.ChoiceField(
        choices=[("open", "Open"), ("resolved", "Resolved"), ("all", "All")],
        required=False,
    )
    sort = forms.ChoiceField(
        choices=[("newest", "Newest"), ("oldest", "Oldest")],
        required=False,
    )

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            self.add_error("date_to", "End date must be on or after the start date.")
        return data
