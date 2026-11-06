from functools import wraps

from django.contrib.auth import SESSION_KEY, logout
from django.http import JsonResponse


def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        user = request.user

        allowed = (
            user.is_authenticated
            and user.is_active
            and user.email_verified
        )

        if not allowed:
            if user.is_authenticated or request.session.get(SESSION_KEY):
                logout(request)

            return JsonResponse(
                {"errors": {"authentication": ["Login is required."]}},
                status=401,
            )

        return view(request, *args, **kwargs)

    return wrapped
