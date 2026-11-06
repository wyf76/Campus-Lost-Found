from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import api_login_required

from .models import Report
from .views import _serialize_report


@never_cache
@require_GET
@api_login_required
def my_reports(request):
    reports = (
        Report.objects.filter(author=request.user)
        .select_related("author")
        .order_by("-created_at", "-pk")
    )
    return JsonResponse({
        "reports": [_serialize_report(report, request) for report in reports],
    })


@never_cache
@require_POST
@csrf_protect
@api_login_required
def resolve_report(request, report_id):
    report = Report.objects.select_related("author").filter(pk=report_id).first()

    if report is None:
        return JsonResponse(
            {"errors": {"report": ["Report not found."]}},
            status=404,
        )

    if report.author_id != request.user.pk and not request.user.is_moderator:
        return JsonResponse(
            {
                "errors": {
                    "authorization": [
                        "Only the owner or a moderator can resolve this report."
                    ]
                }
            },
            status=403,
        )

    Report.objects.filter(pk=report.pk, is_resolved=False).update(is_resolved=True)
    report.is_resolved = True
    return JsonResponse({"report": _serialize_report(report, request)})
