from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Report


class AccountIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(
            email="owner@scu.edu", full_name="Report Owner",
            email_verified=True, is_active=True,
        )
        cls.student = users.create_user(
            email="student@scu.edu", full_name="Other Student",
            email_verified=True, is_active=True,
        )
        cls.moderator = users.create_user(
            email="moderator@scu.edu", full_name="Report Moderator",
            email_verified=True, is_active=True, is_moderator=True,
        )
        cls.report = Report.objects.create(
            author=cls.owner, item_type="lost", title="Keys",
            category="keys", happened_on=date(2026, 10, 25),
            location="learning_commons", description="Blue key ring",
        )

    def test_history_requires_login_and_filters_by_owner(self):
        url = reverse("users:my-reports")
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).json()["reports"], [])
        self.client.force_login(self.owner)
        reports = self.client.get(url).json()["reports"]
        self.assertEqual([report["id"] for report in reports], [self.report.pk])

    def test_only_owner_or_moderator_can_resolve(self):
        url = reverse("items:report-resolve", args=[self.report.pk])
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.report.refresh_from_db()
        self.assertFalse(self.report.is_resolved)
        for actor in (self.owner, self.moderator):
            with self.subTest(actor=actor.pk):
                Report.objects.filter(pk=self.report.pk).update(is_resolved=False)
                self.client.force_login(actor)
                self.assertEqual(self.client.post(url).status_code, 200)
                self.report.refresh_from_db()
                self.assertTrue(self.report.is_resolved)

    def test_block_requires_moderator_and_denies_existing_session(self):
        url = reverse("users:block", args=[self.student.pk])
        student_client = Client()
        student_client.force_login(self.student)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
        self.assertEqual(student_client.get(reverse("users:me")).status_code, 401)
        protected_url = reverse("users:block", args=[self.moderator.pk])
        self.assertEqual(self.client.post(protected_url).status_code, 404)

    def test_resolution_and_blocking_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.moderator)
        for url in (
            reverse("items:report-resolve", args=[self.report.pk]),
            reverse("users:block", args=[self.student.pk]),
        ):
            self.assertEqual(client.post(url).status_code, 403)
