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


from items.account_views import my_reports
from .moderation_views import block_user

urlpatterns += [
    path("me/reports/", my_reports, name="my-reports"),
    path("<int:user_id>/block/", block_user, name="block"),
]
