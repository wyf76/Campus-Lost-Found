import json

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = "River!Cloud92-Lantern"
        self.user = User.objects.create_user(
            email="student@scu.edu",
            full_name="Example Student",
            password=self.password,
            email_verified=True,
            is_active=True,
        )

        self.client = Client(enforce_csrf_checks=True)
        self.client.get(reverse("accounts:csrf"))

        self.login_url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")
        self.me_url = reverse("users:me")

    def post_json(self, url, data):
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

    def login(self, email=None, password=None):
        return self.post_json(
            self.login_url,
            {
                "email": email if email is not None else self.user.email,
                "password": (
                    password if password is not None else self.password
                ),
            },
        )

    def test_verified_user_can_log_in(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session[SESSION_KEY],
            str(self.user.pk),
        )
        self.assertEqual(
            response.json()["user"]["id"],
            self.user.pk,
        )
        self.assertEqual(
            set(response.json()["user"]),
            {
                "id",
                "full_name",
                "email",
                "profile_picture",
                "is_moderator",
            },
        )
        self.assertTrue(
            self.client.cookies[settings.SESSION_COOKIE_NAME]["httponly"]
        )

    def test_login_normalizes_email(self):
        response = self.login(email="  STUDENT@SCU.EDU  ")
        self.assertEqual(response.status_code, 200)

    def test_wrong_password_and_unknown_email_have_same_error(self):
        wrong = self.login(password="Wrong-Password-123!")
        unknown = self.login(email="unknown@scu.edu")

        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(wrong.json(), unknown.json())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_inactive_and_unverified_accounts_cannot_log_in(self):
        for active, verified in (
            (False, True),
            (True, False),
            (False, False),
        ):
            with self.subTest(active=active, verified=verified):
                User.objects.filter(pk=self.user.pk).update(
                    is_active=active,
                    email_verified=verified,
                )
                self.assertEqual(self.login().status_code, 401)
                self.assertNotIn(SESSION_KEY, self.client.session)

    def test_current_user_requires_login(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)

    def test_session_survives_another_request(self):
        self.assertEqual(self.login().status_code, 200)

        # A separate client with the same session cookie represents
        # another request from the same browser.
        another_request = Client(enforce_csrf_checks=True)
        another_request.cookies[settings.SESSION_COOKIE_NAME] = (
            self.client.cookies[settings.SESSION_COOKIE_NAME].value
        )

        response = another_request.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], self.user.pk)

    def test_logout_invalidates_the_old_session(self):
        self.login()
        old_cookie = self.client.cookies[
            settings.SESSION_COOKIE_NAME
        ].value

        response = self.post_json(self.logout_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

        old_session = Client()
        old_session.cookies[settings.SESSION_COOKIE_NAME] = old_cookie
        self.assertEqual(old_session.get(self.me_url).status_code, 401)

    def test_deactivation_stops_an_existing_session(self):
        self.login()
        User.objects.filter(pk=self.user.pk).update(is_active=False)

        self.assertEqual(self.client.get(self.me_url).status_code, 401)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_removing_verification_stops_an_existing_session(self):
        self.login()
        User.objects.filter(pk=self.user.pk).update(email_verified=False)

        self.assertEqual(self.client.get(self.me_url).status_code, 401)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_invalid_login_payloads_are_rejected(self):
        for payload in (
            {},
            [],
            {"email": self.user.email},
            {"email": 123, "password": self.password},
            {"email": self.user.email, "password": None},
            {"email": "student@gmail.com", "password": self.password},
            {
                "email": self.user.email,
                "password": self.password,
                "is_moderator": True,
            },
        ):
            with self.subTest(payload=payload):
                response = self.post_json(self.login_url, payload)
                self.assertEqual(response.status_code, 400)

        malformed = self.client.post(
            self.login_url,
            data="{",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )
        self.assertEqual(malformed.status_code, 400)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_csrf_is_required_for_login_and_logout(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                "email": self.user.email,
                "password": self.password,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

        old_token = self.client.cookies["csrftoken"].value
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(
            old_token,
            self.client.cookies["csrftoken"].value,
        )

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get(self.me_url).status_code, 200)

    def test_method_and_content_type_restrictions(self):
        self.assertEqual(
            self.client.get(self.login_url).status_code,
            405,
        )
        self.assertEqual(
            self.client.get(self.logout_url).status_code,
            405,
        )
        self.assertEqual(
            self.post_json(self.me_url, {}).status_code,
            405,
        )

        response = self.client.post(
            self.login_url,
            data="example",
            content_type="text/plain",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 415)
