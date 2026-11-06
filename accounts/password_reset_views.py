import json
from smtplib import SMTPException

from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .forms import PasswordResetConfirmForm, PasswordResetRequestForm
from .password_reset import (
    request_password_reset_code,
    reset_password_with_code,
)


def _read_form(request, form_class):
    if request.content_type != "application/json":
        return None, JsonResponse(
            {"errors": {"request": ["Send application/json."]}},
            status=415,
        )

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None, JsonResponse(
            {"errors": {"request": ["Invalid JSON."]}},
            status=400,
        )

    form = form_class()

    if (
        not isinstance(data, dict)
        or set(data) != set(form.fields)
        or any(not isinstance(value, str) for value in data.values())
    ):
        return None, JsonResponse(
            {"errors": {"request": ["Send the required string fields only."]}},
            status=400,
        )

    form = form_class(data)

    if not form.is_valid():
        return None, JsonResponse(
            {
                "errors": {
                    field: list(errors)
                    for field, errors in form.errors.items()
                }
            },
            status=400,
        )

    return form.cleaned_data, None


@never_cache
@require_POST
@csrf_protect
def request_reset(request):
    data, error = _read_form(request, PasswordResetRequestForm)

    if error is not None:
        return error

    try:
        request_password_reset_code(data["email"])
    except (SMTPException, OSError):
        return JsonResponse(
            {"errors": {"request": ["Email is temporarily unavailable."]}},
            status=503,
        )

    return JsonResponse({
        "message": (
            "If this email belongs to a verified account and sending limits "
            "allow it, a password-reset email will be sent."
        )
    })


@never_cache
@require_POST
@csrf_protect
def confirm_reset(request):
    data, error = _read_form(request, PasswordResetConfirmForm)

    if error is not None:
        return error

    success = reset_password_with_code(
        email=data["email"],
        code=data["code"],
        new_password=data["new_password"],
    )

    if not success:
        return JsonResponse(
            {
                "errors": {
                    "code": [
                        "The code is invalid, expired, used, or has "
                        "reached its attempt limit."
                    ]
                }
            },
            status=400,
        )

    return JsonResponse({
        "message": "Password reset. Log in again with your new password."
    })
