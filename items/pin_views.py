from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from accounts.permissions import api_login_required

from .models import Report


@never_cache
@require_http_methods(["POST", "DELETE"])
@csrf_protect
@api_login_required
@transaction.atomic
def change_report_pin(request, report_id):
    if not request.user.is_moderator:
        return JsonResponse(
            {"errors": {"authorization": ["Moderator access is required."]}}, status=403,
        )

    report = Report.objects.select_for_update().filter(pk=report_id).first()
    if report is None:
        return JsonResponse(
            {"errors": {"report": ["Report not found."]}}, status=404,
        )

    pinned = request.method == "POST"
    if pinned and report.is_resolved:
        return JsonResponse(
            {"errors": {"report": ["Resolved reports cannot be pinned."]}}, status=409,
        )

    if report.is_pinned != pinned:
        report.is_pinned = pinned
        report.save(update_fields=["is_pinned"])
    return JsonResponse({"is_pinned": report.is_pinned})
