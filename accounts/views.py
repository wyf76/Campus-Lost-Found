import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import RegistrationForm


User = get_user_model()


@never_cache
@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@never_cache
@require_POST
@csrf_protect
def register(request):
    if request.content_type != "application/json":
        return JsonResponse(
            {"errors": {"request": ["Send application/json."]}},
            status=415,
        )

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"errors": {"request": ["Invalid JSON."]}},
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"errors": {"request": ["Send a JSON object."]}},
            status=400,
        )

    allowed_fields = {"full_name", "email", "password"}

    if set(data) - allowed_fields:
        return JsonResponse(
            {
                "errors": {
                    "request": [
                        "Only full_name, email, and password are allowed."
                    ]
                }
            },
            status=400,
        )

    if any(not isinstance(value, str) for value in data.values()):
        return JsonResponse(
            {"errors": {"request": ["All field values must be strings."]}},
            status=400,
        )

    form = RegistrationForm(data)

    if not form.is_valid():
        return JsonResponse(
            {
                "errors": {
                    field: list(errors)
                    for field, errors in form.errors.items()
                }
            },
            status=400,
        )

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                password=form.cleaned_data["password"],
                email_verified=False,
                is_active=False,
                is_moderator=False,
                is_staff=False,
                is_superuser=False,
            )
    except ValidationError as error:
        errors = (
            error.message_dict
            if hasattr(error, "message_dict")
            else {"request": error.messages}
        )
        return JsonResponse({"errors": errors}, status=400)
    except IntegrityError:
        # Handles duplicate requests arriving at the same time.
        return JsonResponse(
            {
                "errors": {
                    "email": ["An account with this email already exists."]
                }
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": (
                "Account created. Email verification is required before login."
            ),
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            },
        },
        status=201,
    )


import re
from smtplib import SMTPException

from django.core.validators import validate_email

from .models import validate_scu_email
from .verification import request_verification_code, verify_email_code


def _verification_payload(request, require_code=False):
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

    expected = {"email", "code"} if require_code else {"email"}

    if (
        not isinstance(data, dict)
        or set(data) != expected
        or any(not isinstance(value, str) for value in data.values())
    ):
        return None, JsonResponse(
            {"errors": {"request": ["Send the required string fields only."]}},
            status=400,
        )

    data["email"] = data["email"].strip().lower()

    try:
        validate_email(data["email"])
        validate_scu_email(data["email"])
    except ValidationError:
        return None, JsonResponse(
            {"errors": {"email": ["Enter a valid @scu.edu email address."]}},
            status=400,
        )

    if require_code and re.fullmatch(r"[0-9]{6}", data["code"]) is None:
        return None, JsonResponse(
            {"errors": {"code": ["Enter the six-digit code as a string."]}},
            status=400,
        )

    return data, None


@never_cache
@require_POST
@csrf_protect
def request_email_verification(request):
    data, error = _verification_payload(request)

    if error is not None:
        return error

    try:
        request_verification_code(data["email"])
    except (SMTPException, OSError):
        return JsonResponse(
            {"errors": {"request": ["Email is temporarily unavailable."]}},
            status=503,
        )

    # Same response for unknown, verified, and rate-limited accounts.
    return JsonResponse({
        "message": (
            "If this account needs verification and sending limits allow it, "
            "a verification email will be sent."
        )
    })


@never_cache
@require_POST
@csrf_protect
def verify_email(request):
    data, error = _verification_payload(request, require_code=True)

    if error is not None:
        return error

    if not verify_email_code(data["email"], data["code"]):
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
        "message": "Email verified. You can now log in."
    })


from django.contrib.auth import (
    authenticate,
    login as django_login,
    logout as django_logout,
)

from .forms import LoginForm
from .permissions import api_login_required


def _current_user_data(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "profile_picture": user.profile_picture,
        "is_moderator": user.is_moderator,
    }


@never_cache
@require_POST
@csrf_protect
def login_user(request):
    if request.content_type != "application/json":
        return JsonResponse(
            {"errors": {"request": ["Send application/json."]}},
            status=415,
        )

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"errors": {"request": ["Invalid JSON."]}},
            status=400,
        )

    if (
        not isinstance(data, dict)
        or set(data) != {"email", "password"}
        or any(not isinstance(value, str) for value in data.values())
    ):
        return JsonResponse(
            {
                "errors": {
                    "request": ["Send email and password as strings only."]
                }
            },
            status=400,
        )

    form = LoginForm(data)

    if not form.is_valid():
        return JsonResponse(
            {
                "errors": {
                    field: list(errors)
                    for field, errors in form.errors.items()
                }
            },
            status=400,
        )

    user = authenticate(
        request,
        email=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
    )

    if user is None or not user.is_active or not user.email_verified:
        return JsonResponse(
            {
                "errors": {
                    "authentication": ["Unable to log in with these credentials."]
                }
            },
            status=401,
        )

    django_login(request, user)

    return JsonResponse({
        "message": "Logged in.",
        "user": _current_user_data(user),
        "csrfToken": get_token(request),
    })


@never_cache
@require_POST
@csrf_protect
def logout_user(request):
    django_logout(request)

    return JsonResponse({
        "message": "Logged out.",
        "csrfToken": get_token(request),
    })


@never_cache
@require_GET
@api_login_required
def current_user(request):
    return JsonResponse({
        "user": _current_user_data(request.user),
    })
