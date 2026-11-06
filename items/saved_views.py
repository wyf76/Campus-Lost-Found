from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods

from accounts.permissions import api_login_required

from .models import Report, SavedReport
from .views import _serialize_report


@never_cache
@require_GET
@api_login_required
def saved_report_list(request):
    saved = (
        SavedReport.objects.filter(user=request.user)
        .select_related("report", "report__author")
        .order_by("-saved_at", "-pk")
    )
    return JsonResponse({
        "reports": [_serialize_report(entry.report, request) for entry in saved],
    })


@never_cache
@require_http_methods(["POST", "DELETE"])
@csrf_protect
@api_login_required
@transaction.atomic
def saved_report_change(request, report_id):
    if not Report.objects.select_for_update().filter(pk=report_id).exists():
        return JsonResponse(
            {"errors": {"report": ["Report not found."]}}, status=404,
        )

    if request.method == "POST":
        SavedReport.objects.get_or_create(user=request.user, report_id=report_id)
        return JsonResponse({"saved": True})

    SavedReport.objects.filter(user=request.user, report_id=report_id).delete()
    return JsonResponse({"saved": False})
