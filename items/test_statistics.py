from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ReportFlag
from .tests import create_report, create_user


class PlatformStatisticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = create_user("student@scu.edu")
        cls.moderator = create_user("moderator@scu.edu")
        cls.moderator.is_moderator = True
        cls.moderator.save(update_fields=["is_moderator"])

    def test_statistics_require_moderator_access(self):
        url = reverse("platform-statistics")
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_counts_include_zeroes_and_use_current_database_state(self):
        self.client.force_login(self.moderator)
        url = reverse("platform-statistics")
        empty = self.client.get(url)
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(
            empty.json()["reports"],
            {"total": 0, "lost": 0, "found": 0, "open": 0, "resolved": 0},
        )

        blocked = create_user("blocked@scu.edu")
        blocked.is_active = False
        blocked.save(update_fields=["is_active"])
        lost = create_report(self.student)
        found = create_report(self.student, item_type="found", is_resolved=True)
        ReportFlag.objects.create(report=lost, reporter=blocked, reason="Spam")
        ReportFlag.objects.create(
            report=found, reporter=blocked, reason="Spam", escalated_at=timezone.now(),
        )

        self.assertEqual(self.client.get(url).json(), {
            "reports": {"total": 2, "lost": 1, "found": 1, "open": 1, "resolved": 1},
            "students": {"total": 2, "verified": 2, "active_verified": 1},
            "flags": {"total": 2, "escalated": 1},
        })
