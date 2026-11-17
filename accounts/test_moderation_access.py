from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class StudentAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.moderator = users.create_user(
            "moderator@scu.edu", "Moderator",
            email_verified=True, is_active=True, is_moderator=True,
        )
        cls.student = users.create_user(
            "student@scu.edu", "Student", email_verified=True, is_active=True,
        )
        cls.blocked = users.create_user(
            "blocked@scu.edu", "Blocked Student", email_verified=True,
        )
        cls.unverified = users.create_user("unverified@scu.edu", "Unverified Student")
        cls.staff = users.create_user(
            "staff@scu.edu", "Staff", email_verified=True, is_staff=True,
        )

    def setUp(self):
        self.blocked_url = reverse("users:blocked-students")
        self.unblock_url = reverse("users:unblock", args=[self.blocked.pk])

    def test_blocked_list_and_unblock_require_moderator_access(self):
        for user, status in ((None, 401), (self.student, 403)):
            with self.subTest(user=user):
                if user:
                    self.client.force_login(user)
                self.assertEqual(self.client.get(self.blocked_url).status_code, status)
                self.assertEqual(self.client.post(self.unblock_url).status_code, status)
        self.blocked.refresh_from_db()
        self.assertFalse(self.blocked.is_active)

    def test_unblock_restores_access_and_updates_list(self):
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.get(self.blocked_url).json(), {
            "students": [{
                "id": self.blocked.pk,
                "full_name": self.blocked.full_name,
                "email": self.blocked.email,
            }],
        })
        for _ in range(2):
            self.assertEqual(self.client.post(self.unblock_url).status_code, 200)
        self.blocked.refresh_from_db()
        self.assertTrue(self.blocked.is_active)
        self.assertEqual(self.client.get(self.blocked_url).json(), {"students": []})

    def test_unblock_requires_csrf_and_rejects_ineligible_accounts(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.moderator)
        self.assertEqual(client.post(self.unblock_url).status_code, 403)
        self.client.force_login(self.moderator)
        for user in (self.unverified, self.staff, self.moderator):
            with self.subTest(user=user):
                url = reverse("users:unblock", args=[user.pk])
                self.assertEqual(self.client.post(url).status_code, 404)
