import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_message_alert(recipient_email):
    try:
        delivered = send_mail(
            subject="Campus Lost and Found: new chat message",
            message="You have a new message. Sign in to Campus Lost and Found to read it.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
        )
    except (SMTPException, OSError):
        delivered = 0

    if not delivered:
        logger.warning("Chat message email alert was not sent.")
