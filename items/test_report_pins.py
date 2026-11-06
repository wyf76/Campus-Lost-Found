from django.test import TestCase
from django.urls import reverse

from .tests import create_report, create_user


class ReportPinTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = create_user("student@scu.edu")
        cls.moderator = create_user("moderator@scu.edu")
        cls.moderator.is_moderator = True
        cls.moderator.save(update_fields=["is_moderator"])
        cls.older = create_report(cls.student, title="Older report")
        cls.newer = create_report(cls.student, title="Newer report")
        cls.pin = reverse("items:report-pin", args=[cls.older.pk])
        cls.feed = reverse("items:report-list-create")

    def report_ids(self, params=None):
        return [report["id"] for report in self.client.get(self.feed, params).json()["reports"]]

    def test_only_moderators_can_pin_and_default_feed_prioritizes_pins(self):
        self.assertEqual(self.client.post(self.pin).status_code, 401)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.pin).status_code, 403)

        self.client.force_login(self.moderator)
        self.assertEqual(self.client.post(self.pin).json(), {"is_pinned": True})
        self.assertEqual(self.report_ids(), [self.older.pk, self.newer.pk])
        self.assertEqual(
            self.report_ids({"sort": "newest"}), [self.newer.pk, self.older.pk],
        )
        self.assertEqual(self.client.delete(self.pin).json(), {"is_pinned": False})
        self.assertEqual(self.report_ids(), [self.newer.pk, self.older.pk])

    def test_resolving_clears_pin_and_resolved_reports_cannot_be_pinned(self):
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.post(self.pin).status_code, 200)

        self.client.force_login(self.student)
        resolve = reverse("items:report-resolve", args=[self.older.pk])
        response = self.client.post(resolve)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["report"]["is_pinned"])
        self.older.refresh_from_db()
        self.assertFalse(self.older.is_pinned)

        self.client.force_login(self.moderator)
        self.assertEqual(self.client.post(self.pin).status_code, 409)
