import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from accounts.permissions import api_login_required

from .forms import ReportForm
from .models import Report
from .views import _form_errors, _serialize_report


class ReportEditForm(ReportForm):
    class Meta(ReportForm.Meta):
        fields = (
            "title", "category", "happened_on",
            "location", "location_details", "description",
        )


@never_cache
@require_http_methods(["PATCH"])
@csrf_protect
@api_login_required
def edit_report(request, report_id):
    if request.content_type != "application/json":
        return JsonResponse(
            {"errors": {"request": ["Send application/json."]}}, status=415,
        )

    try:
        changes = json.loads(request.body)
    except ValueError:
        return JsonResponse(
            {"errors": {"request": ["Invalid JSON."]}}, status=400,
        )

    fields = ReportEditForm.Meta.fields
    if (
        not isinstance(changes, dict)
        or not changes
        or set(changes).difference(fields)
        or any(not isinstance(value, str) for value in changes.values())
    ):
        return JsonResponse(
            {"errors": {"request": ["Supply editable fields with string values."]}},
            status=400,
        )

    with transaction.atomic():
        report = Report.objects.select_for_update().filter(pk=report_id).first()

        if report is None:
            return JsonResponse(
                {"errors": {"report": ["Report not found."]}}, status=404,
            )

        if report.author_id != request.user.pk:
            return JsonResponse(
                {"errors": {"authorization": ["Only the author can edit this report."]}},
                status=403,
            )

        if report.is_resolved:
            return JsonResponse(
                {"errors": {"report": ["Resolved reports cannot be edited."]}},
                status=409,
            )

        data = {field: getattr(report, field) for field in fields}
        data.update(changes)
        form = ReportEditForm(data, instance=report)

        if not form.is_valid():
            return JsonResponse({"errors": _form_errors(form)}, status=400)

        report = form.save()

    return JsonResponse({"report": _serialize_report(report, request)})
