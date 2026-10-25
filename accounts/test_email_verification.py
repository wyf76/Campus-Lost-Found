import json
from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerification


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class EmailVerificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@scu.edu",
            full_name="Example Student",
            password="River!Cloud92-Lantern",
        )
        self.client = Client(enforce_csrf_checks=True)
        self.token = self.client.get(
            reverse("accounts:csrf")
        ).json()["csrfToken"]
        self.request_url = reverse("accounts:verification-request")
        self.confirm_url = reverse("accounts:verification-confirm")

    def post_json(self, url, data):
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )

    def request_code(self, number=123456):
        with patch(
            "accounts.verification.secrets.randbelow",
            return_value=number,
        ):
            return self.post_json(
                self.request_url,
                {"email": self.user.email},
            )

    def confirm(self, code="123456"):
        return self.post_json(
            self.confirm_url,
            {"email": self.user.email, "code": code},
        )

    def allow_resend(self):
        EmailVerification.objects.filter(user=self.user).update(
            sent_at=timezone.now() - timedelta(seconds=61),
        )

    def test_delivery_hash_activation_and_reuse(self):
        response = self.request_code()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("123456", mail.outbox[0].body)
        self.assertNotIn("123456", response.content.decode())

        state = EmailVerification.objects.get(user=self.user)
        self.assertNotEqual(state.code_hash, "123456")

        self.assertEqual(self.confirm().status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.is_active)

        # Replaying a code must not reactivate a blocked account.
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        self.assertEqual(self.confirm().status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_expired_code_is_rejected(self):
        self.request_code()
        EmailVerification.objects.filter(user=self.user).update(
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        self.assertEqual(self.confirm().status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.assertFalse(self.user.is_active)

    def test_five_wrong_attempts_lock_the_code(self):
        self.request_code()

        for _ in range(5):
            self.assertEqual(self.confirm("654321").status_code, 400)

        self.assertEqual(self.confirm().status_code, 400)
        self.assertEqual(
            EmailVerification.objects.get(user=self.user).attempts,
            5,
        )

    def test_resend_wait_and_old_code_invalidation(self):
        self.request_code()
        self.request_code(number=654321)
        self.assertEqual(len(mail.outbox), 1)

        self.allow_resend()
        self.request_code(number=654321)
        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(self.confirm("123456").status_code, 400)
        self.assertEqual(self.confirm("654321").status_code, 200)

    def test_hourly_sending_limit(self):
        for _ in range(5):
            self.request_code()
            self.allow_resend()

        self.request_code()
        self.assertEqual(len(mail.outbox), 5)

        EmailVerification.objects.filter(user=self.user).update(
            window_started_at=timezone.now() - timedelta(hours=1),
        )
        self.request_code()
        self.assertEqual(len(mail.outbox), 6)

    def test_unknown_and_verified_accounts_get_generic_response(self):
        unknown = self.post_json(
            self.request_url,
            {"email": "unknown@scu.edu"},
        )

        self.user.email_verified = True
        self.user.save(update_fields=["email_verified"])
        verified = self.request_code()

        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.json(), verified.json())
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_does_not_use_sending_quota(self):
        with patch(
            "accounts.verification.send_mail",
            side_effect=SMTPException("Test failure"),
        ):
            response = self.request_code()

        self.assertEqual(response.status_code, 503)
        state = EmailVerification.objects.get(user=self.user)
        self.assertEqual(state.send_count, 0)
        self.assertEqual(state.code_hash, "")

    def test_csrf_and_input_validation(self):
        for url, payload in (
            (self.request_url, {"email": self.user.email}),
            (
                self.confirm_url,
                {"email": self.user.email, "code": "123456"},
            ),
        ):
            response = self.client.post(
                url,
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 403)

        self.assertEqual(
            self.post_json(
                self.request_url,
                {"email": "student@gmail.com"},
            ).status_code,
            400,
        )
        self.assertEqual(self.confirm("12345").status_code, 400)
        self.assertEqual(self.confirm(123456).status_code, 400)
        self.assertEqual(
            self.post_json(
                self.confirm_url,
                {
                    "email": self.user.email,
                    "code": "123456",
                    "is_active": True,
                },
            ).status_code,
            400,
        )
