import json

from django import forms
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import api_login_required

from .models import Report, ReportFlag
from .views import _form_errors


class ReportFlagForm(forms.ModelForm):
    class Meta:
        model = ReportFlag
        fields = ("reason",)


@never_cache
@require_POST
@csrf_protect
@api_login_required
@transaction.atomic
def flag_report(request, report_id):
    if request.content_type != "application/json":
        return JsonResponse(
            {"errors": {"request": ["Send application/json."]}}, status=415,
        )

    try:
        data = json.loads(request.body)
    except ValueError:
        data = None
    if (
        not isinstance(data, dict)
        or set(data) != {"reason"}
        or not isinstance(data["reason"], str)
    ):
        return JsonResponse(
            {"errors": {"request": ["Supply a reason as a string."]}}, status=400,
        )

    form = ReportFlagForm(data)
    if not form.is_valid():
        return JsonResponse({"errors": _form_errors(form)}, status=400)

    if not Report.objects.select_for_update().filter(pk=report_id).exists():
        return JsonResponse(
            {"errors": {"report": ["Report not found."]}}, status=404,
        )

    flag, created = ReportFlag.objects.get_or_create(
        report_id=report_id,
        reporter=request.user,
        defaults={"reason": form.cleaned_data["reason"]},
    )
    return JsonResponse({"flag_id": flag.pk}, status=201 if created else 200)


@never_cache
@require_GET
@api_login_required
def report_flag_list(request):
    if not request.user.is_moderator:
        return JsonResponse(
            {"errors": {"authorization": ["Moderator access is required."]}}, status=403,
        )

    flags = ReportFlag.objects.select_related("report").order_by("-created_at", "-pk")
    return JsonResponse({
        "flags": [
            {
                "id": flag.pk,
                "report_id": flag.report_id,
                "report_title": flag.report.title,
                "reporter_id": flag.reporter_id,
                "reason": flag.reason,
                "created_at": flag.created_at.isoformat(),
            }
            for flag in flags
        ],
    })
