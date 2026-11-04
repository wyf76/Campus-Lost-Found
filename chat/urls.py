from django.urls import path

from . import views


app_name = "chat"

urlpatterns = [
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
