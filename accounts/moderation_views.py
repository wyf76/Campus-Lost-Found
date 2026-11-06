from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .permissions import api_login_required


@never_cache
@require_POST
@csrf_protect
@api_login_required
def block_user(request, user_id):
    if not request.user.is_moderator:
        return JsonResponse(
            {"errors": {"authorization": ["Moderator access is required."]}},
            status=403,
        )

    updated = get_user_model().objects.filter(
        pk=user_id,
        email_verified=True,
        is_moderator=False,
        is_staff=False,
        is_superuser=False,
    ).exclude(pk=request.user.pk).update(is_active=False)

    if not updated:
        return JsonResponse(
            {"errors": {"user": ["No eligible verified student was found."]}},
            status=404,
        )

    return JsonResponse({"message": "User blocked.", "user_id": user_id})
