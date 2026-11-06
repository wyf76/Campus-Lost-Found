from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import validate_scu_email


User = get_user_model()


class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)
    password = forms.CharField(
        min_length=8,
        max_length=128,
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        validate_scu_email(email)

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")

        if password:
            candidate = User(
                email=cleaned.get("email", ""),
                full_name=cleaned.get("full_name", ""),
            )

            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password = forms.CharField(
        max_length=128,
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        validate_scu_email(email)
        return email


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(max_length=254)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        validate_scu_email(email)
        return email


class PasswordResetConfirmForm(PasswordResetRequestForm):
    code = forms.RegexField(
        regex=r"^[0-9]{6}$",
        min_length=6,
        max_length=6,
        strip=False,
    )
    new_password = forms.CharField(
        min_length=8,
        max_length=128,
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("new_password")

        if email and password:
            candidate = (
                User.objects.filter(email=email).first()
                or User(email=email)
            )

            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                self.add_error("new_password", error)

        return cleaned
