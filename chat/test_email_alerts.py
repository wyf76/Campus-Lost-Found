from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Conversation, Message, MessageNotification
from .tests import create_report, create_user


class MessageEmailAlertTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user("owner@scu.edu", "Report Owner")
        cls.seeker = create_user("seeker@scu.edu", "Seeker")
        conversation = Conversation.objects.create(
            report=create_report(cls.owner), seeker=cls.seeker,
        )
        cls.url = reverse("chat:message-list-create", args=[conversation.pk])

    def send(self, body):
        return self.client.post(self.url, {"body": body}, content_type="application/json")

    def test_alert_is_deferred_and_omits_private_message_text(self):
        self.client.force_login(self.seeker)
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.send("Private pickup instructions")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertNotIn("Private pickup instructions", mail.outbox[0].body)

    def test_failed_email_leaves_message_and_notification_saved(self):
        self.client.force_login(self.seeker)
        with patch("chat.email_alerts.send_mail", side_effect=SMTPException):
            with self.assertLogs("chat.email_alerts", level="WARNING"):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.send("Hello")

        self.assertEqual(response.status_code, 201)
        message = Message.objects.get(pk=response.json()["message"]["id"])
        self.assertTrue(MessageNotification.objects.filter(message=message).exists())

    def test_inactive_recipient_and_invalid_message_do_not_schedule_alerts(self):
        self.client.force_login(self.seeker)
        with self.captureOnCommitCallbacks(execute=True) as invalid_callbacks:
            self.assertEqual(self.send("").status_code, 400)
        self.assertEqual(invalid_callbacks, [])

        self.owner.is_active = False
        self.owner.save(update_fields=["is_active"])
        with self.captureOnCommitCallbacks(execute=True) as inactive_callbacks:
            self.assertEqual(self.send("Hello").status_code, 201)
        self.assertEqual(inactive_callbacks, [])
