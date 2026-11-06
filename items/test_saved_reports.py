from django.test import Client, TestCase
from django.urls import reverse

from .models import SavedReport
from .tests import create_report, create_user


class SavedReportTests(TestCase):
    def setUp(self):
        self.owner = create_user("owner@scu.edu")
        self.reader = create_user("reader@scu.edu")
        self.report = create_report(self.owner)
        self.saved = reverse("items:saved-report-list")
        self.save = reverse("items:saved-report-change", args=[self.report.pk])

    def test_save_and_unsave_are_private_and_repeatable(self):
        self.client.force_login(self.reader)
        for _ in range(2):
            self.assertEqual(self.client.post(self.save).json(), {"saved": True})
        self.assertEqual(SavedReport.objects.count(), 1)

        self.report.is_resolved = True
        self.report.save(update_fields=["is_resolved"])
        reports = self.client.get(self.saved).json()["reports"]
        self.assertEqual([report["id"] for report in reports], [self.report.pk])
        self.assertTrue(reports[0]["is_resolved"])

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.saved).json()["reports"], [])
        self.assertEqual(self.client.delete(self.save).json(), {"saved": False})
        self.assertEqual(SavedReport.objects.count(), 1)

        self.client.force_login(self.reader)
        for _ in range(2):
            self.assertEqual(self.client.delete(self.save).json(), {"saved": False})
        self.assertEqual(self.client.get(self.saved).json()["reports"], [])
        self.assertEqual(SavedReport.objects.count(), 0)

    def test_authentication_csrf_and_missing_report(self):
        self.assertEqual(self.client.get(self.saved).status_code, 401)
        self.assertEqual(self.client.post(self.save).status_code, 401)

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.reader)
        self.assertEqual(csrf_client.post(self.save).status_code, 403)
        self.assertEqual(csrf_client.delete(self.save).status_code, 403)

        self.client.force_login(self.reader)
        missing = reverse("items:saved-report-change", args=[self.report.pk + 1])
        self.assertEqual(self.client.post(missing).status_code, 404)
        self.assertFalse(SavedReport.objects.exists())
