from functools import wraps

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .permissions import api_login_required


def _moderator_required(view):
    @api_login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_moderator:
            return JsonResponse(
                {"errors": {"authorization": ["Moderator access is required."]}},
                status=403,
            )
        return view(request, *args, **kwargs)

    return wrapped


def _eligible_students():
    return get_user_model().objects.filter(
        email_verified=True,
        is_moderator=False,
        is_staff=False,
        is_superuser=False,
    )


def _set_student_access(user_id, *, active):
    updated = _eligible_students().filter(pk=user_id).update(is_active=active)
    if not updated:
        return JsonResponse(
            {"errors": {"user": ["No eligible verified student was found."]}},
            status=404,
        )

    message = "User unblocked." if active else "User blocked."
    return JsonResponse({"message": message, "user_id": user_id})


@never_cache
@require_POST
@csrf_protect
@_moderator_required
def block_user(request, user_id):
    return _set_student_access(user_id, active=False)


@never_cache
@require_POST
@csrf_protect
@_moderator_required
def unblock_user(request, user_id):
    return _set_student_access(user_id, active=True)


@never_cache
@require_GET
@_moderator_required
def blocked_students(request):
    students = _eligible_students().filter(is_active=False)
    return JsonResponse({
        "students": list(students.order_by("full_name", "pk").values("id", "full_name", "email")),
    })
