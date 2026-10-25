import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class ProfileTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            email="viewer@scu.edu",
            full_name="Viewing Student",
            password="River!Cloud92-Lantern",
            email_verified=True,
            is_active=True,
        )
        self.other = User.objects.create_user(
            email="other@scu.edu",
            full_name="Another Student",
            password="Forest!Moon83-Window",
            profile_picture="https://example.com/avatar.png",
            email_verified=True,
            is_active=True,
        )

        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.viewer)
        self.client.get(reverse("accounts:csrf"))

        self.own_url = reverse(
            "users:profile",
            kwargs={"user_id": self.viewer.pk},
        )
        self.other_url = reverse(
            "users:profile",
            kwargs={"user_id": self.other.pk},
        )
        self.me_url = reverse("users:me")

    def test_anonymous_user_cannot_view_profiles(self):
        anonymous = Client()
        response = anonymous.get(self.other_url)

        self.assertEqual(response.status_code, 401)

    def test_student_can_view_own_public_profile(self):
        response = self.client.get(self.own_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], self.viewer.pk)
        self.assertEqual(
            response.json()["user"]["full_name"],
            self.viewer.full_name,
        )

    def test_student_can_view_another_public_profile(self):
        response = self.client.get(self.other_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["user"],
            {
                "id": self.other.pk,
                "full_name": self.other.full_name,
                "email": self.other.email,
                "profile_picture": self.other.profile_picture,
            },
        )

    def test_missing_profile_returns_404(self):
        url = reverse(
            "users:profile",
            kwargs={"user_id": self.other.pk + 10000},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["errors"]["profile"],
            ["Profile not found."],
        )

    def test_inactive_and_unverified_profiles_are_hidden(self):
        for active, verified in (
            (False, True),
            (True, False),
            (False, False),
        ):
            with self.subTest(active=active, verified=verified):
                User.objects.filter(pk=self.other.pk).update(
                    is_active=active,
                    email_verified=verified,
                )

                response = self.client.get(self.other_url)
                self.assertEqual(response.status_code, 404)

    def test_blocked_viewer_cannot_view_profiles(self):
        User.objects.filter(pk=self.viewer.pk).update(is_active=False)

        response = self.client.get(self.other_url)
        self.assertEqual(response.status_code, 401)

    def test_unverified_viewer_cannot_view_profiles(self):
        User.objects.filter(pk=self.viewer.pk).update(
            email_verified=False,
        )

        response = self.client.get(self.other_url)
        self.assertEqual(response.status_code, 401)

    def assert_profile_edits_rejected(self):
        before = list(User.objects.order_by("pk").values())

        payload = {
            "full_name": "Changed Name",
            "email": "changed@scu.edu",
            "profile_picture": "https://example.com/changed.png",
            "password": "Changed!Password92",
            "is_moderator": True,
            "is_staff": True,
            "is_superuser": True,
            "is_active": False,
            "email_verified": False,
        }

        for method in ("POST", "PUT", "PATCH", "DELETE"):
            for url in (self.own_url, self.other_url, self.me_url):
                with self.subTest(method=method, url=url):
                    response = self.client.generic(
                        method,
                        url,
                        data=json.dumps(payload),
                        content_type="application/json",
                        HTTP_X_CSRFTOKEN=(
                            self.client.cookies["csrftoken"].value
                        ),
                    )
                    self.assertEqual(response.status_code, 405)

        after = list(User.objects.order_by("pk").values())
        self.assertEqual(before, after)

    def test_students_cannot_edit_profiles(self):
        self.assert_profile_edits_rejected()

    def test_moderators_cannot_edit_profiles(self):
        self.viewer.is_moderator = True
        self.viewer.save(update_fields=["is_moderator"])

        self.assert_profile_edits_rejected()
