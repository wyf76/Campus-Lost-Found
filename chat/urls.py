from django.urls import path

from . import notification_views, views


app_name = "chat"

urlpatterns = [
    path("notifications/", notification_views.notification_list, name="notification-list"),
    path(
        "notifications/<int:notification_id>/read/",
        notification_views.notification_read,
        name="notification-read",
    ),
    path(
        "reports/<int:report_id>/conversations/",
        views.conversation_start,
        name="conversation-start",
    ),
    path("conversations/", views.conversation_list, name="conversation-list"),
    path(
        "conversations/<int:conversation_id>/messages/",
        views.message_collection,
        name="message-list-create",
    ),
]
