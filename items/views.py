import json

from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)

from accounts.permissions import api_login_required

from .forms import ReportForm, ReportSearchForm
from .models import Report

# define what fields are allowed in a report form submission, and which are allowed in JSON submissions
REPORT_FORM_FIELDS = {
    "item_type",
    "title",
    "category",
    "happened_on",
    "location",
    "location_details",
    "description",
    "image",
}
JSON_REPORT_FIELDS = REPORT_FORM_FIELDS - {"image"}

# check get or post method and dispatch to the appropriate function
@never_cache
@require_http_methods(["GET", "POST"])
def report_collection(request):
    """Dispatch collection requests to the list or create endpoint."""
    if request.method == "GET":
        return report_list(request)
    return report_create(request)

#convert a report object to a JSON serializable dictionary
def _serialize_report(report, request):
    """Return the public JSON representation of a report."""
    image_url = None
    if report.image:
        image_url = request.build_absolute_uri(report.image.url)

    return {
        "id": report.id,
        "item_type": report.item_type,
        "item_type_display": report.get_item_type_display(),
        "title": report.title,
        "category": report.category,
        "category_display": report.get_category_display(),
        "happened_on": report.happened_on.isoformat(),
        "location": report.location,
        "location_display": report.get_location_display(),
        "location_details": report.location_details,
        "description": report.description,
        "author": {
            "id": report.author_id,
            "full_name": report.author.full_name,
        },
        "is_resolved": report.is_resolved,
        "created_at": report.created_at.isoformat(),
        "image_url": image_url,
    }

# handle form errors and return them as a dictionary of field names to error messages
def _form_errors(form):
    return {
        field: [str(error) for error in errors]
        for field, errors in form.errors.items()
    }


@never_cache
@require_POST
@csrf_protect
@api_login_required
def report_create(request):
    """Create a report from JSON text fields or a multipart form upload."""
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse(
                {"errors": {"request": ["Invalid JSON."]}},
                status=400,
            )

        if not isinstance(data, dict):
            return JsonResponse(
                {"errors": {"request": ["Send a JSON object."]}},
                status=400,
            )

        if any(not isinstance(value, str) for value in data.values()):
            return JsonResponse(
                {"errors": {"request": ["All report values must be strings."]}},
                status=400,
            )

        unexpected = set(data) - JSON_REPORT_FIELDS
        if unexpected:
            return JsonResponse(
                {
                    "errors": {
                        "request": [
                            "JSON reports accept only report text fields; "
                            "send images as multipart/form-data."
                        ]
                    }
                },
                status=400,
            )
        files = None
    elif request.content_type == "multipart/form-data":
        data = request.POST
        files = request.FILES
        unexpected = (set(data) | set(files)) - REPORT_FORM_FIELDS
        if unexpected:
            return JsonResponse(
                {"errors": {"request": ["Unexpected report field."]}},
                status=400,
            )
    else:
        return JsonResponse(
            {
                "errors": {
                    "request": [
                        "Send application/json or multipart/form-data."
                    ]
                }
            },
            status=415,
        )

    form = ReportForm(data, files)
    if not form.is_valid():
        return JsonResponse({"errors": _form_errors(form)}, status=400)

    report = form.save(commit=False)
    report.author = request.user
    report.save()

    return JsonResponse(
        {"report": _serialize_report(report, request)},
        status=201,
    )


@never_cache
@require_GET
def report_list(request):
    """Return matching reports, showing open reports by default."""
    form = ReportSearchForm({key: value.strip() for key, value in request.GET.items()})
    if set(request.GET) - set(form.fields):
        return JsonResponse(
            {"errors": {"request": ["Unsupported search parameter."]}},
            status=400,
        )
    if not form.is_valid():
        return JsonResponse({"errors": _form_errors(form)}, status=400)

    data = form.cleaned_data
    reports = Report.objects.select_related("author")
    query = data["q"]
    if query:
        reports = reports.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
            | Q(location_details__icontains=query)
        )
    if data["type"]:
        reports = reports.filter(item_type=data["type"])
    if data["category"]:
        reports = reports.filter(category=data["category"])
    if data["location"]:
        reports = reports.filter(location=data["location"])
    if data["date_from"]:
        reports = reports.filter(happened_on__gte=data["date_from"])
    if data["date_to"]:
        reports = reports.filter(happened_on__lte=data["date_to"])

    status = data["status"] or "open"
    if status != "all":
        reports = reports.filter(is_resolved=(status == "resolved"))

    ordering = ("created_at", "pk") if data["sort"] == "oldest" else ("-created_at", "-pk")
    return JsonResponse(
        {"reports": [_serialize_report(report, request) for report in reports.order_by(*ordering)]}
    )


@never_cache
@require_GET
def report_detail(request, report_id):
    """Return one report by its database ID, or a JSON 404 response."""
    report = (
        Report.objects.select_related("author")
        .filter(pk=report_id)
        .first()
    )
    if report is None:
        return JsonResponse(
            {"errors": {"report": ["Report not found."]}},
            status=404,
        )

    report_data = _serialize_report(report, request)
    # The frontend can POST to this endpoint to open or create the chat.
    report_data["chat_start_url"] = request.build_absolute_uri(
        reverse("chat:conversation-start", args=[report.pk])
    )
    return JsonResponse({"report": report_data})
