from smtplib import SMTPException

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from accounts.permissions import api_login_required

from .models import ReportFlag


@never_cache
@require_POST
@csrf_protect
@api_login_required
@transaction.atomic
def escalate_flag(request, flag_id):
    if not request.user.is_moderator:
        return JsonResponse(
            {"errors": {"authorization": ["Moderator access is required."]}}, status=403,
        )

    flag = (
        ReportFlag.objects.select_for_update(of=("self",))
        .select_related("report__author")
        .filter(pk=flag_id)
        .first()
    )
    if flag is None:
        return JsonResponse(
            {"errors": {"flag": ["Flag not found."]}}, status=404,
        )
    if flag.escalated_at:
        return JsonResponse({"escalated_at": flag.escalated_at.isoformat()})

    recipient = settings.CAMPUS_MODERATION_EMAIL
    try:
        validate_email(recipient)
    except ValidationError:
        return JsonResponse(
            {"errors": {"email": ["Configure a university moderation email address."]}},
            status=503,
        )
    if settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
        return JsonResponse(
            {"errors": {"email": ["Enable SMTP to escalate flags."]}}, status=503,
        )

    try:
        delivered = send_mail(
            subject=f"Campus Lost and Found: flagged report #{flag.report_id}",
            message=(
                f"Flag ID: {flag.pk}\n"
                f"Report: {flag.report.title}\n"
                f"Report author: {flag.report.author.email}\n"
                f"Flag reason: {flag.reason}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
    except (SMTPException, OSError):
        delivered = 0
    if not delivered:
        return JsonResponse(
            {"errors": {"email": ["The email could not be sent."]}}, status=502,
        )

    flag.escalated_at = timezone.now()
    flag.save(update_fields=["escalated_at"])
    return JsonResponse({"escalated_at": flag.escalated_at.isoformat()})
