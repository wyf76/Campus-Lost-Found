from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .permissions import api_login_required


User = get_user_model()


@never_cache
@require_GET
@api_login_required
def public_profile(request, user_id):
    profile = (
        User.objects.filter(
            pk=user_id,
            is_active=True,
            email_verified=True,
        )
        .values("id", "full_name", "email", "profile_picture")
        .first()
    )

    if profile is None:
        return JsonResponse(
            {"errors": {"profile": ["Profile not found."]}},
            status=404,
        )

    return JsonResponse({"user": profile})
