import json
from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import SESSION_KEY, authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerification, PasswordResetCode


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.old_password = "River!Cloud92-Lantern"
        self.new_password = "Forest!Moon83-Window"

        self.user = User.objects.create_user(
            email="student@scu.edu",
            full_name="Example Student",
            password=self.old_password,
            email_verified=True,
            is_active=True,
        )

        self.client = Client(enforce_csrf_checks=True)
        self.client.get(reverse("accounts:csrf"))

        self.request_url = reverse("accounts:password-reset-request")
        self.confirm_url = reverse("accounts:password-reset-confirm")

    def post_json(self, url, data):
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

    def request_code(self, number=123456, email=None):
        with patch(
            "accounts.password_reset.secrets.randbelow",
            return_value=number,
        ):
            return self.post_json(
                self.request_url,
                {"email": email if email is not None else self.user.email},
            )

    def confirm(self, code="123456", password=None):
        return self.post_json(
            self.confirm_url,
            {
                "email": self.user.email,
                "code": code,
                "new_password": (
                    password if password is not None else self.new_password
                ),
            },
        )

    def allow_resend(self):
        PasswordResetCode.objects.filter(user=self.user).update(
            sent_at=timezone.now() - timedelta(seconds=61),
        )

    def test_delivery_hash_and_response_privacy(self):
        response = self.request_code(email="  STUDENT@SCU.EDU  ")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("123456", mail.outbox[0].body)
        self.assertNotIn("123456", response.content.decode())

        state = PasswordResetCode.objects.get(user=self.user)
        self.assertNotEqual(state.code_hash, "123456")

    def test_unknown_and_unverified_accounts_get_generic_response(self):
        unknown = self.request_code(email="unknown@scu.edu")

        User.objects.create_user(
            email="pending@scu.edu",
            full_name="Pending Student",
            password=self.old_password,
        )
        pending = self.request_code(email="pending@scu.edu")

        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.json(), pending.json())
        self.assertEqual(len(mail.outbox), 0)

    def test_success_changes_only_password_and_code_cannot_be_reused(self):
        fields = (
            "id", "email", "full_name", "profile_picture",
            "is_active", "email_verified", "is_moderator",
            "is_staff", "is_superuser",
        )
        before = User.objects.filter(pk=self.user.pk).values(*fields).get()

        self.request_code()
        response = self.confirm()

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertFalse(self.user.check_password(self.old_password))
        self.assertNotIn(SESSION_KEY, self.client.session)

        after = User.objects.filter(pk=self.user.pk).values(*fields).get()
        self.assertEqual(before, after)
        self.assertEqual(self.confirm().status_code, 400)

    def test_expired_code_is_rejected(self):
        self.request_code()
        PasswordResetCode.objects.filter(user=self.user).update(
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        self.assertEqual(self.confirm().status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.old_password))

    def test_five_wrong_attempts_lock_the_code(self):
        self.request_code()

        for _ in range(5):
            self.assertEqual(self.confirm(code="654321").status_code, 400)

        self.assertEqual(self.confirm().status_code, 400)
        self.assertEqual(
            PasswordResetCode.objects.get(user=self.user).attempts,
            5,
        )

    def test_resend_wait_and_replacement(self):
        self.request_code()
        self.request_code(number=654321)
        self.assertEqual(len(mail.outbox), 1)

        self.allow_resend()
        self.request_code(number=654321)
        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(self.confirm(code="123456").status_code, 400)
        self.assertEqual(self.confirm(code="654321").status_code, 200)

    def test_hourly_sending_limit(self):
        for _ in range(5):
            self.request_code()
            self.allow_resend()

        self.request_code()
        self.assertEqual(len(mail.outbox), 5)

        PasswordResetCode.objects.filter(user=self.user).update(
            window_started_at=timezone.now() - timedelta(hours=1, seconds=1),
        )
        self.request_code()
        self.assertEqual(len(mail.outbox), 6)

    def test_weak_password_does_not_consume_code(self):
        self.request_code()

        response = self.confirm(password="123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.json()["errors"])
        self.assertEqual(
            PasswordResetCode.objects.get(user=self.user).attempts,
            0,
        )

        self.assertEqual(self.confirm().status_code, 200)

    def test_existing_sessions_are_invalidated(self):
        browsers = [Client(), Client()]
        me_url = reverse("users:me")

        for browser in browsers:
            browser.force_login(self.user)
            self.assertEqual(browser.get(me_url).status_code, 200)

        self.request_code()
        self.assertEqual(self.confirm().status_code, 200)

        for browser in browsers:
            self.assertEqual(browser.get(me_url).status_code, 401)

        self.assertIsNone(
            authenticate(email=self.user.email, password=self.old_password)
        )
        self.assertIsNotNone(
            authenticate(email=self.user.email, password=self.new_password)
        )

    def test_reset_does_not_unblock_account(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)

        self.request_code()
        self.assertEqual(self.confirm().status_code, 200)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertIsNone(
            authenticate(email=self.user.email, password=self.new_password)
        )

    def test_registration_code_cannot_reset_password(self):
        verification = EmailVerification.objects.create(
            user=self.user,
            code_hash=make_password("999999"),
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        self.request_code()
        self.assertEqual(self.confirm(code="999999").status_code, 400)
        self.assertEqual(self.confirm(code="123456").status_code, 200)

        verification.refresh_from_db()
        self.assertIsNone(verification.consumed_at)

    def test_csrf_input_and_method_restrictions(self):
        for url, payload in (
            (self.request_url, {"email": self.user.email}),
            (
                self.confirm_url,
                {
                    "email": self.user.email,
                    "code": "123456",
                    "new_password": self.new_password,
                },
            ),
        ):
            self.assertEqual(self.client.get(url).status_code, 405)
            response = self.client.post(
                url,
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 403)

        for payload in (
            {},
            [],
            {"email": "student@gmail.com"},
            {"email": self.user.email, "is_active": True},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.post_json(self.request_url, payload).status_code,
                    400,
                )

        self.assertEqual(self.confirm(code="12345").status_code, 400)
        self.assertEqual(self.confirm(code=123456).status_code, 400)

        for content_type, data, expected in (
            ("application/json", "{", 400),
            ("text/plain", "example", 415),
        ):
            response = self.client.post(
                self.request_url,
                data=data,
                content_type=content_type,
                HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
            )
            self.assertEqual(response.status_code, expected)

    def test_email_failure_does_not_use_sending_quota(self):
        with patch(
            "accounts.password_reset.send_mail",
            side_effect=SMTPException("Test failure"),
        ):
            response = self.request_code()

        self.assertEqual(response.status_code, 503)
        state = PasswordResetCode.objects.get(user=self.user)
        self.assertEqual(state.send_count, 0)
        self.assertEqual(state.code_hash, "")
