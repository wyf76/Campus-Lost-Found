from django.test import TestCase
from django.urls import reverse

from .models import Conversation, MessageNotification
from .tests import create_report, create_user


class MessageNotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user("owner@scu.edu", "Report Owner")
        cls.seeker = create_user("seeker@scu.edu", "Seeker")
        cls.report = create_report(cls.owner)
        cls.conversation = Conversation.objects.create(
            report=cls.report, seeker=cls.seeker,
        )
        cls.messages = reverse("chat:message-list-create", args=[cls.conversation.pk])
        cls.notifications = reverse("chat:notification-list")

    def send(self, body):
        return self.client.post(
            self.messages, {"body": body}, content_type="application/json",
        )

    def test_notifications_go_to_the_other_participant_and_can_be_marked_read(self):
        self.assertEqual(self.client.get(self.notifications).status_code, 401)
        self.client.force_login(self.seeker)
        sent = self.send("I found your backpack.")
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(self.client.get(self.notifications).json()["notifications"], [])
        notification = MessageNotification.objects.get()
        read_url = reverse("chat:notification-read", args=[notification.pk])
        self.assertEqual(self.client.post(read_url).status_code, 404)

        self.client.force_login(self.owner)
        unread = self.client.get(self.notifications).json()["notifications"]
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread[0]["message_id"], sent.json()["message"]["id"])
        self.assertEqual(unread[0]["conversation_id"], self.conversation.pk)
        self.assertEqual(self.client.post(read_url).status_code, 200)
        self.assertEqual(self.client.post(read_url).status_code, 200)
        self.assertEqual(self.client.get(self.notifications).json()["notifications"], [])
        self.assertEqual(self.send("Thank you!").status_code, 201)

        self.client.force_login(self.seeker)
        unread = self.client.get(self.notifications).json()["notifications"]
        self.assertEqual([entry["sender_name"] for entry in unread], ["Report Owner"])

    def test_rejected_message_creates_no_notification(self):
        self.client.force_login(self.seeker)
        self.assertEqual(self.send("").status_code, 400)
        self.assertFalse(MessageNotification.objects.exists())
