from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase


User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="  Student@SCU.EDU  ",
            full_name="Example Student",
            password="Example-Only-Password-123!",
        )

    def test_account_fields_and_password(self):
        self.user.refresh_from_db()

        self.assertIsInstance(self.user.id, int)
        self.assertEqual(self.user.email, "student@scu.edu")
        self.assertEqual(self.user.full_name, "Example Student")
        self.assertTrue(
            self.user.check_password("Example-Only-Password-123!")
        )
        self.assertNotEqual(
            self.user.password,
            "Example-Only-Password-123!",
        )
        self.assertFalse(self.user.email_verified)
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_moderator)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_non_scu_email_is_rejected(self):
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                email="student@gmail.com",
                full_name="Another Student",
                password="Example-Only-Password-123!",
            )

    def test_blank_name_is_rejected(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="another@scu.edu",
                full_name="   ",
                password="Example-Only-Password-123!",
            )

    def test_database_rejects_case_variant_duplicate(self):
        # bulk_create bypasses our manager and save method, so this
        # checks the database constraint itself.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.bulk_create([
                    User(
                        email="STUDENT@SCU.EDU",
                        full_name="Duplicate Student",
                        password="!",
                    ),
                ])


class RegistrationTests(TestCase):
    def setUp(self):
        from django.test import Client
        from django.urls import reverse

        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse("accounts:register")
        response = self.client.get(reverse("accounts:csrf"))
        self.token = response.json()["csrfToken"]

        self.payload = {
            "full_name": "Example Student",
            "email": "student@scu.edu",
            "password": "River!Cloud92-Lantern",
        }

    def post_json(self, payload):
        import json

        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )

    def test_success_creates_unverified_unprivileged_account(self):
        response = self.post_json(self.payload)
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email="student@scu.edu")
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertFalse(user.email_verified)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_moderator)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        self.assertEqual(
            set(response.json()["user"]),
            {"id", "full_name", "email"},
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_duplicate_email_ignores_case(self):
        self.assertEqual(self.post_json(self.payload).status_code, 201)

        duplicate = dict(self.payload, email="STUDENT@SCU.EDU")
        self.assertEqual(self.post_json(duplicate).status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_email_is_rejected(self):
        for email in (
            "student@gmail.com",
            "student@scu.edu.example.com",
            "student@sub.scu.edu",
            "not-an-email",
        ):
            with self.subTest(email=email):
                response = self.post_json(dict(self.payload, email=email))
                self.assertEqual(response.status_code, 400)

        self.assertEqual(User.objects.count(), 0)

    def test_weak_password_is_rejected(self):
        response = self.post_json(dict(self.payload, password="123"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json()["errors"])
        self.assertEqual(User.objects.count(), 0)

    def test_missing_blank_and_non_string_fields_are_rejected(self):
        for payload in (
            {},
            dict(self.payload, full_name="   "),
            dict(self.payload, email=123),
            dict(self.payload, password=None),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.post_json(payload).status_code, 400)

        self.assertEqual(User.objects.count(), 0)

    def test_permission_fields_are_rejected(self):
        for field in (
            "is_moderator",
            "is_staff",
            "is_superuser",
            "is_active",
            "email_verified",
        ):
            with self.subTest(field=field):
                payload = dict(self.payload)
                payload[field] = True
                self.assertEqual(self.post_json(payload).status_code, 400)

        self.assertEqual(User.objects.count(), 0)

    def test_csrf_token_is_required(self):
        import json

        response = self.client.post(
            self.url,
            data=json.dumps(self.payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 0)

    def test_request_format_and_method(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

        malformed = self.client.post(
            self.url,
            data="{",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(malformed.status_code, 400)

        wrong_type = self.client.post(
            self.url,
            data="example",
            content_type="text/plain",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(wrong_type.status_code, 415)

        self.assertEqual(self.post_json([]).status_code, 400)
