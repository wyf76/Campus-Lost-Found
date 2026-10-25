import secrets
from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import EmailVerification


User = get_user_model()


def request_verification_code(email):
    user = User.objects.filter(
        email=email,
        email_verified=False,
    ).first()

    if user is None:
        return False

    state, _ = EmailVerification.objects.get_or_create(user=user)
    now = timezone.now()

    if state.sent_at and now < state.sent_at + timedelta(seconds=60):
        return False

    new_window = now >= state.window_started_at + timedelta(hours=1)

    if not new_window and state.send_count >= 5:
        return False

    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = make_password(code)

    with transaction.atomic():
        updated = EmailVerification.objects.filter(
            pk=state.pk,
            revision=state.revision,
            user__email_verified=False,
        ).update(
            code_hash=code_hash,
            expires_at=now + timedelta(minutes=10),
            attempts=0,
            consumed_at=None,
            sent_at=now,
            window_started_at=now if new_window else state.window_started_at,
            send_count=1 if new_window else state.send_count + 1,
            revision=F("revision") + 1,
        )

        if updated != 1:
            return False

        delivered = send_mail(
            subject="Campus Lost and Found: verify your email",
            message=(
                f"Your verification code is: {code}\n\n"
                "This code expires in 10 minutes and can be used once.\n"
                "If you did not request this, you can ignore this message."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        if delivered != 1:
            raise SMTPException("The email backend did not accept the message.")

    return True


def verify_email_code(email, code):
    state = EmailVerification.objects.filter(
        user__email=email,
        user__email_verified=False,
    ).first()

    if state is None or not state.code_hash:
        return False

    # Reserve an attempt before checking the code.
    reserved = EmailVerification.objects.filter(
        pk=state.pk,
        code_hash=state.code_hash,
        consumed_at__isnull=True,
        expires_at__gt=timezone.now(),
        attempts__lt=5,
        user__email_verified=False,
    ).update(
        attempts=F("attempts") + 1,
        revision=F("revision") + 1,
    )

    if reserved != 1:
        return False

    if not check_password(code, state.code_hash):
        return False

    with transaction.atomic():
        # Only one request can consume the current code.
        consumed = EmailVerification.objects.filter(
            pk=state.pk,
            code_hash=state.code_hash,
            consumed_at__isnull=True,
            expires_at__gt=timezone.now(),
            user__email_verified=False,
        ).update(
            consumed_at=timezone.now(),
            revision=F("revision") + 1,
        )

        if consumed != 1:
            return False

        activated = User.objects.filter(
            pk=state.user_id,
            email_verified=False,
        ).update(
            email_verified=True,
            is_active=True,
        )

    return activated == 1
