from django import forms
from django.core.exceptions import ValidationError


class StrictStringField(forms.CharField):
    """A CharField that rejects JSON numbers, arrays, and objects."""

    def to_python(self, value):
        if value is None:
            return ""
        if not isinstance(value, str):
            raise ValidationError("Enter a valid string.", code="invalid")
        return super().to_python(value)


class MessageForm(forms.Form):
    body = StrictStringField(max_length=4000, strip=True)
