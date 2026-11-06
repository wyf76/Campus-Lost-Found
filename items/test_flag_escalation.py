from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ReportFlag
from .tests import create_report, create_user


@override_settings(CAMPUS_MODERATION_EMAIL="staff@example.org")
class FlagEscalationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = create_user("student@scu.edu")
        author = create_user("author@scu.edu")
        cls.moderator = create_user("moderator@scu.edu")
        cls.moderator.is_moderator = True
        cls.moderator.save(update_fields=["is_moderator"])
        cls.flag = ReportFlag.objects.create(
            report=create_report(author), reporter=cls.student, reason="Spam",
        )
        cls.url = reverse("items:flag-escalate", args=[cls.flag.pk])

    def test_only_moderator_can_send_and_repeat_returns_same_timestamp(self):
        self.assertEqual(self.client.post(self.url).status_code, 401)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

        self.client.force_login(self.moderator)
        first = self.client.post(self.url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self.client.post(self.url).json(), first.json())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["staff@example.org"])
        self.assertIn("author@scu.edu", mail.outbox[0].body)
        self.assertNotIn(self.student.email, mail.outbox[0].body)
        self.flag.refresh_from_db()
        self.assertEqual(first.json()["escalated_at"], self.flag.escalated_at.isoformat())

    def test_missing_configuration_or_smtp_failure_keeps_flag_unsent(self):
        self.client.force_login(self.moderator)
        with self.settings(CAMPUS_MODERATION_EMAIL=""):
            self.assertEqual(self.client.post(self.url).status_code, 503)
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"):
            self.assertEqual(self.client.post(self.url).status_code, 503)
        with patch("items.escalation_views.send_mail", side_effect=SMTPException):
            self.assertEqual(self.client.post(self.url).status_code, 502)
        self.flag.refresh_from_db()
        self.assertIsNone(self.flag.escalated_at)
        self.assertEqual(len(mail.outbox), 0)
