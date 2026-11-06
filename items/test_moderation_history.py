from django.test import TestCase
from django.urls import reverse

from .tests import create_report, create_user


class ModerationReportHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = create_user("student@scu.edu")
        other = create_user("other@scu.edu")
        cls.moderator = create_user("moderator@scu.edu")
        cls.moderator.is_moderator = True
        cls.moderator.save(update_fields=["is_moderator"])
        cls.open_report = create_report(cls.student, title="Backpack")
        cls.resolved_report = create_report(other, title="Notebook", is_resolved=True)

    def test_requires_moderator_and_student_feed_still_defaults_to_open(self):
        url = reverse("moderation-report-history")
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 403)

        response = self.client.get(reverse("items:report-list-create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [report["id"] for report in response.json()["reports"]],
            [self.open_report.pk],
        )

    def test_history_defaults_to_all_and_reuses_report_filters(self):
        self.client.force_login(self.moderator)
        url = reverse("moderation-report-history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [report["id"] for report in response.json()["reports"]],
            [self.resolved_report.pk, self.open_report.pk],
        )

        filtered = self.client.get(url, {"status": "resolved", "q": "notebook"})
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(
            [report["id"] for report in filtered.json()["reports"]],
            [self.resolved_report.pk],
        )
        self.assertEqual(self.client.get(url, {"status": "invalid"}).status_code, 400)
        self.assertEqual(self.client.post(url).status_code, 405)
