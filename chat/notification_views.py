from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import api_login_required

from .models import MessageNotification


@never_cache
@require_GET
@api_login_required
def notification_list(request):
    unread = MessageNotification.objects.filter(
        recipient=request.user, read_at__isnull=True,
    ).select_related("message", "message__sender").order_by("-pk")

    return JsonResponse({
        "notifications": [
            {
                "id": notification.pk,
                "conversation_id": notification.message.conversation_id,
                "message_id": notification.message_id,
                "sender_name": notification.message.sender.full_name,
                "created_at": notification.message.created_at.isoformat(),
            }
            for notification in unread[:50]
        ],
    })


@never_cache
@require_POST
@csrf_protect
@api_login_required
def notification_read(request, notification_id):
    notification = MessageNotification.objects.filter(
        pk=notification_id, recipient=request.user,
    )
    if not notification.exists():
        return JsonResponse(
            {"errors": {"notification": ["Notification not found."]}}, status=404,
        )

    notification.filter(read_at__isnull=True).update(read_at=timezone.now())
    return JsonResponse({"read": True})
