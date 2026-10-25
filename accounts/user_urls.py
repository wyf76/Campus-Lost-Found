from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("me/", views.current_user, name="me"),
]

from . import profile_views

urlpatterns += [
    path(
        "<int:user_id>/",
        profile_views.public_profile,
        name="profile",
    ),
]
