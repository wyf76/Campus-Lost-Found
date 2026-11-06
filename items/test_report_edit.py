from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Report


class ReportEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(
            email="owner@scu.edu", full_name="Owner",
            email_verified=True, is_active=True,
        )
        cls.other = users.create_user(
            email="other@scu.edu", full_name="Other",
            email_verified=True, is_active=True, is_moderator=True,
        )
        cls.report = Report.objects.create(
            author=cls.owner, item_type="lost", title="Keys",
            category="keys", happened_on=date(2026, 10, 25),
            location="learning_commons", description="Blue key ring",
        )
        cls.url = reverse("items:report-edit", args=[cls.report.pk])

    def patch(self, data, client=None):
        client = self.client if client is None else client
        return client.patch(self.url, data, content_type="application/json")

    def test_owner_can_edit_selected_fields(self):
        self.client.force_login(self.owner)
        response = self.patch({"title": "Car keys", "happened_on": "2026-10-26"})
        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.title, "Car keys")
        self.assertEqual(self.report.happened_on, date(2026, 10, 26))
        self.assertEqual(self.report.author_id, self.owner.pk)
        self.assertEqual(self.report.item_type, "lost")
        self.assertEqual(self.report.description, "Blue key ring")

    def test_owner_can_set_preserve_and_clear_time(self):
        self.client.force_login(self.owner)
        for changes, expected in (
            ({"happened_time": "09:15"}, "09:15:00"),
            ({"title": "Car keys"}, "09:15:00"),
            ({"happened_time": ""}, None),
        ):
            with self.subTest(changes=changes):
                response = self.patch(changes)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["report"]["happened_time"], expected)

    def test_only_owner_can_edit(self):
        self.assertEqual(self.patch({"title": "Changed"}).status_code, 401)
        self.client.force_login(self.other)
        self.assertEqual(self.patch({"title": "Changed"}).status_code, 403)

    def test_invalid_immutable_and_resolved_updates_are_rejected(self):
        self.client.force_login(self.owner)
        for data in ({"title": ""}, {"item_type": "found"}, {"happened_on": "bad"}):
            self.assertEqual(self.patch(data).status_code, 400)
        Report.objects.filter(pk=self.report.pk).update(is_resolved=True)
        self.assertEqual(self.patch({"title": "Changed"}).status_code, 409)
        self.report.refresh_from_db()
        self.assertEqual(self.report.title, "Keys")

    def test_edit_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(self.patch({"title": "Changed"}, client).status_code, 403)
