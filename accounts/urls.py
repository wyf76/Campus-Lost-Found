from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("csrf/", views.csrf_token, name="csrf"),
    path("register/", views.register, name="register"),
]

urlpatterns += [
    path(
        "verification/request/",
        views.request_email_verification,
        name="verification-request",
    ),
    path(
        "verification/confirm/",
        views.verify_email,
        name="verification-confirm",
    ),
]

urlpatterns += [
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
]

from . import password_reset_views

urlpatterns += [
    path(
        "password-reset/request/",
        password_reset_views.request_reset,
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        password_reset_views.confirm_reset,
        name="password-reset-confirm",
    ),
]
