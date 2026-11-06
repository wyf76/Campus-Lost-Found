import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from items.models import Report

from .forms import MessageForm
from .models import Conversation, Message

User = get_user_model()


# Create a verified, active user for the tests.
def create_user(email, full_name):
    return User.objects.create_user(
        email=email,
        full_name=full_name,
        password="test-password-123",
        is_active=True,
        email_verified=True,
    )


# Create a report that can be used to test chat conversations.
def create_report(author):
    return Report.objects.create(
        item_type="lost",
        title="Blue backpack",
        category="bags",
        happened_on="2026-10-25",
        location="learning_commons",
        location_details="",
        description="A blue backpack.",
        author=author,
    )


# Test validation rules for chat message text.
class MessageFormTests(TestCase):
    def test_accepts_normal_message(self):
        form = MessageForm(data={"body": "Hello, I found your report."})

        # A normal message should pass validation and remain unchanged.
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["body"], "Hello, I found your report.")

    def test_strips_leading_and_trailing_whitespace(self):
        form = MessageForm(data={"body": "  Hello  "})

        # Leading and trailing spaces should be removed.
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["body"], "Hello")

    def test_rejects_empty_and_whitespace_only_messages(self):
        # Check an empty string, spaces, and newline/tab characters.
        for body in ("", "   ", "\n\t"):
            with self.subTest(body=repr(body)):
                form = MessageForm(data={"body": body})

                # Empty or whitespace-only messages should be rejected.
                self.assertFalse(form.is_valid())
                self.assertIn("body", form.errors)

    def test_rejects_none_and_non_string_values(self):
        # Message text must be a string, not None, a number, a list, or a dictionary.
        for body in (None, 123, ["message"], {"text": "message"}):
            with self.subTest(body=body):
                form = MessageForm(data={"body": body})

                self.assertFalse(form.is_valid())
                self.assertIn("body", form.errors)

    def test_message_length_boundary(self):
        # 4,000 characters is allowed; 4,001 characters exceeds the limit.
        valid_form = MessageForm(data={"body": "x" * 4000})
        invalid_form = MessageForm(data={"body": "x" * 4001})

        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("body", invalid_form.errors)


# Test database relationships and rules for conversations and messages.
class ChatModelTests(TestCase):
    def setUp(self):
        # Prepare the report author, the person starting the chat, and their report.
        self.reporter = create_user("reporter@scu.edu", "Report Author")
        self.seeker = create_user("seeker@scu.edu", "Report Seeker")
        self.report = create_report(self.reporter)

        # Create a conversation between the report and the seeker.
        self.conversation = Conversation.objects.create(
            report=self.report,
            seeker=self.seeker,
        )

    def test_conversation_links_report_and_seeker(self):
        # The conversation should point to the expected report and seeker.
        self.assertEqual(self.conversation.report, self.report)
        self.assertEqual(self.conversation.seeker, self.seeker)

    def test_report_and_seeker_pair_must_be_unique(self):
        # The database should reject a duplicate conversation for this report and seeker.
        with self.assertRaises(IntegrityError):
            # Roll back the transaction after the expected database error.
            with transaction.atomic():
                Conversation.objects.create(
                    report=self.report,
                    seeker=self.seeker,
                )

    def test_conversation_timestamps_are_created(self):
        # Both timestamps should be set automatically when the conversation is created.
        self.assertIsNotNone(self.conversation.created_at)
        self.assertIsNotNone(self.conversation.updated_at)

    def test_message_links_conversation_and_sender(self):
        # Create a message in the conversation.
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.seeker,
            body="Hello",
        )

        # Check the message's conversation, sender, and creation time.
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.seeker)
        self.assertIsNotNone(message.created_at)

    def test_message_model_validates_body_length_boundary(self):
        # Build messages at and beyond the 4,000-character limit.
        valid_message = Message(
            conversation=self.conversation,
            sender=self.seeker,
            body="x" * 4000,
        )
        invalid_message = Message(
            conversation=self.conversation,
            sender=self.seeker,
            body="x" * 4001,
        )

        # The message at the limit should pass model validation.
        valid_message.full_clean()

        # The message over the limit should raise a validation error.
        with self.assertRaises(ValidationError):
            invalid_message.full_clean()


# Test chat API authentication, conversation creation, messages, and access control.
class ChatApiTests(TestCase):
    def setUp(self):
        # Prepare the report author, chat seeker, and an unrelated user.
        self.reporter = create_user("reporter@scu.edu", "Report Author")
        self.seeker = create_user("seeker@scu.edu", "Report Seeker")
        self.outsider = create_user("outsider@scu.edu", "Other Student")
        self.report = create_report(self.reporter)

        # Build the API URL for starting a conversation about this report.
        self.start_url = reverse(
            "chat:conversation-start",
            args=[self.report.pk],
        )

        # Build the API URL for the logged-in user's conversation list.
        self.list_url = reverse("chat:conversation-list")

    def post_json(self, url, payload):
        # Send a JSON POST request using Django's test client.
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_chat_endpoints_require_login(self):
        # Create a conversation so the message endpoint has a valid conversation ID.
        conversation = Conversation.objects.create(
            report=self.report,
            seeker=self.seeker,
        )
        messages_url = reverse(
            "chat:message-list-create",
            args=[conversation.pk],
        )

        # Make requests without logging in.
        start_response = self.client.post(self.start_url)
        list_response = self.client.get(self.list_url)
        messages_response = self.client.get(messages_url)

        # All chat endpoints should require authentication.
        self.assertEqual(start_response.status_code, 401)
        self.assertEqual(list_response.status_code, 401)
        self.assertEqual(messages_response.status_code, 401)

    def test_seeker_creates_and_reuses_conversation(self):
        # Log in as the person who wants to contact the report author.
        self.client.force_login(self.seeker)

        # Start the same conversation twice.
        first_response = self.client.post(self.start_url)
        second_response = self.client.post(self.start_url)

        # The first request creates a conversation; the second reuses it.
        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)

        # Both responses should refer to the same conversation.
        self.assertEqual(
            first_response.json()["conversation"]["id"],
            second_response.json()["conversation"]["id"],
        )

        # Only one conversation should exist in the database.
        self.assertEqual(Conversation.objects.count(), 1)

    def test_author_cannot_chat_with_self_and_missing_report_returns_404(self):
        # Log in as the report author.
        self.client.force_login(self.reporter)

        # The author should not be allowed to start a chat with themselves.
        own_report_response = self.client.post(self.start_url)

        # Try to start a conversation for a report that does not exist.
        missing_report_response = self.client.post(
            reverse("chat:conversation-start", args=[999999])
        )

        self.assertEqual(own_report_response.status_code, 400)
        self.assertEqual(missing_report_response.status_code, 404)

        # Neither invalid request should create a conversation.
        self.assertEqual(Conversation.objects.count(), 0)

    def test_message_creation_sets_sender_and_rejects_invalid_payloads(self):
        # Create a conversation and get its message API URL.
        conversation = Conversation.objects.create(
            report=self.report,
            seeker=self.seeker,
        )
        messages_url = reverse(
            "chat:message-list-create",
            args=[conversation.pk],
        )

        # Log in as the seeker, who will send the message.
        self.client.force_login(self.seeker)

        # Try to provide a sender ID in the request, which should not be allowed.
        response = self.post_json(
            messages_url,
            {"body": "  Hello reporter  ", "sender": self.reporter.pk},
        )
        self.assertEqual(response.status_code, 400)

        # Send a valid message without specifying the sender.
        response = self.post_json(messages_url, {"body": "  Hello reporter  "})
        self.assertEqual(response.status_code, 201)

        # The server should set the sender from the logged-in user and trim whitespace.
        message = Message.objects.get()
        self.assertEqual(message.sender, self.seeker)
        self.assertEqual(message.body, "Hello reporter")

        # These invalid message bodies should all be rejected.
        invalid_values = (None, 5, ["hello"], "   ", "x" * 4001)
        for body in invalid_values:
            with self.subTest(body_type=type(body).__name__):
                response = self.post_json(messages_url, {"body": body})
                self.assertEqual(response.status_code, 400)

    def test_only_participants_can_access_conversation_messages(self):
        # Create a conversation and one message in it.
        conversation = Conversation.objects.create(
            report=self.report,
            seeker=self.seeker,
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.seeker,
            body="Hello reporter",
        )
        messages_url = reverse(
            "chat:message-list-create",
            args=[conversation.pk],
        )

        # Log in as an unrelated user and try to read or send messages.
        self.client.force_login(self.outsider)
        outsider_messages = self.client.get(messages_url)
        outsider_conversations = self.client.get(self.list_url)
        outsider_send = self.post_json(messages_url, {"body": "Intruding"})

        # The outsider cannot access another user's conversation or messages.
        self.assertEqual(outsider_messages.status_code, 404)
        self.assertEqual(outsider_conversations.json()["conversations"], [])
        self.assertEqual(outsider_send.status_code, 404)

        # The report author is a conversation participant and can read its messages.
        self.client.force_login(self.reporter)
        reporter_messages = self.client.get(messages_url)
        self.assertEqual(reporter_messages.status_code, 200)
        self.assertEqual(len(reporter_messages.json()["messages"]), 1)

class ResolvedReportChatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reporter = create_user("reporter@scu.edu", "Reporter")
        cls.seeker = create_user("seeker@scu.edu", "Seeker")
        cls.report = create_report(cls.reporter)

    def resolve_report(self):
        self.client.force_login(self.reporter)
        url = reverse("items:report-resolve", args=[self.report.pk])
        self.assertEqual(self.client.post(url).status_code, 200)

    def test_resolved_report_rejects_new_conversation(self):
        self.resolve_report()
        self.client.force_login(self.seeker)
        url = reverse("chat:conversation-start", args=[self.report.pk])
        self.assertEqual(self.client.post(url).status_code, 409)
        self.assertFalse(Conversation.objects.filter(report=self.report).exists())

    def test_existing_conversation_can_be_reopened_and_read(self):
        conversation = Conversation.objects.create(report=self.report, seeker=self.seeker)
        message = Message.objects.create(
            conversation=conversation, sender=self.seeker, body="I found your bag.",
        )
        self.resolve_report()
        self.client.force_login(self.seeker)
        start_url = reverse("chat:conversation-start", args=[self.report.pk])
        reopened = self.client.post(start_url)
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json()["conversation"]["id"], conversation.pk)

        url = reverse("chat:message-list-create", args=[conversation.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry["id"] for entry in response.json()["messages"]], [message.pk])

    def test_neither_participant_can_send_after_resolution(self):
        conversation = Conversation.objects.create(report=self.report, seeker=self.seeker)
        self.resolve_report()
        url = reverse("chat:message-list-create", args=[conversation.pk])

        for user in (self.reporter, self.seeker):
            with self.subTest(user=user.pk):
                self.client.force_login(user)
                response = self.client.post(
                    url, {"body": "A new reply"}, content_type="application/json",
                )
                self.assertEqual(response.status_code, 409)

        self.assertFalse(conversation.messages.exists())
