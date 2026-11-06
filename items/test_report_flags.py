from django.test import Client, TestCase
from django.urls import reverse

from .models import ReportFlag
from .tests import create_report, create_user


class ReportFlagTests(TestCase):
    def setUp(self):
        self.owner = create_user("owner@scu.edu")
        self.reader = create_user("reader@scu.edu")
        self.moderator = create_user("moderator@scu.edu")
        self.moderator.is_moderator = True
        self.moderator.save(update_fields=["is_moderator"])
        self.report = create_report(self.owner)
        self.submit = reverse("items:report-flag", args=[self.report.pk])
        self.queue = reverse("items:report-flag-list")

    def flag(self, reason):
        return self.client.post(
            self.submit, {"reason": reason}, content_type="application/json",
        )

    def test_submission_is_repeatable_and_queue_is_private(self):
        self.assertEqual(self.flag("Spam").status_code, 401)
        self.assertEqual(self.client.get(self.queue).status_code, 401)
        self.client.force_login(self.reader)
        first = self.flag("  Spam  ")
        repeated = self.flag("Another reason")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.json(), repeated.json())
        self.assertEqual(ReportFlag.objects.count(), 1)
        self.assertEqual(self.client.get(self.queue).status_code, 403)

        self.client.force_login(self.moderator)
        response = self.client.get(self.queue)
        self.assertEqual(response.status_code, 200)
        flag, = response.json()["flags"]
        self.assertEqual(flag["report_id"], self.report.pk)
        self.assertEqual(flag["reporter_id"], self.reader.pk)
        self.assertEqual(flag["reason"], "Spam")

    def test_invalid_reasons_and_missing_csrf_are_rejected(self):
        self.client.force_login(self.reader)
        for reason in (" ", "x" * 501, 123):
            with self.subTest(reason=reason):
                self.assertEqual(self.flag(reason).status_code, 400)

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.reader)
        response = csrf_client.post(
            self.submit, {"reason": "Spam"}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ReportFlag.objects.exists())
