from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from accounts.permissions import api_login_required

from .models import Report, ReportFlag


@never_cache
@require_GET
@api_login_required
def platform_statistics(request):
    if not request.user.is_moderator:
        return JsonResponse(
            {"errors": {"authorization": ["Moderator access is required."]}}, status=403,
        )

    reports = Report.objects.aggregate(
        total=Count("pk"),
        lost=Count("pk", filter=Q(item_type=Report.ItemType.LOST)),
        found=Count("pk", filter=Q(item_type=Report.ItemType.FOUND)),
        open=Count("pk", filter=Q(is_resolved=False)),
        resolved=Count("pk", filter=Q(is_resolved=True)),
    )
    students = get_user_model().objects.filter(
        is_moderator=False, is_staff=False, is_superuser=False,
    ).aggregate(
        total=Count("pk"),
        verified=Count("pk", filter=Q(email_verified=True)),
        active_verified=Count("pk", filter=Q(email_verified=True, is_active=True)),
    )
    flags = ReportFlag.objects.aggregate(
        total=Count("pk"),
        escalated=Count("pk", filter=Q(escalated_at__isnull=False)),
    )
    return JsonResponse({"reports": reports, "students": students, "flags": flags})
