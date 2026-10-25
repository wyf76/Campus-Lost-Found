import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env.backend", interpolate=False)


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"Set {name} in your environment or .env.backend."
        )
    return value


SECRET_KEY = required_env("CAMPUS_DJANGO_SECRET_KEY")

# Local development settings
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": required_env("CAMPUS_DB_NAME"),
        "USER": required_env("CAMPUS_DB_USER"),
        "PASSWORD": required_env("CAMPUS_DB_PASSWORD"),
        "HOST": os.environ.get("CAMPUS_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("CAMPUS_DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

email_mode = os.environ.get(
    "CAMPUS_EMAIL_BACKEND", "console"
).strip().lower()

if email_mode not in {"console", "smtp"}:
    raise ImproperlyConfigured(
        "CAMPUS_EMAIL_BACKEND must be console or smtp."
    )

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if email_mode == "smtp"
    else "django.core.mail.backends.console.EmailBackend"
)

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.environ.get(
    "CAMPUS_EMAIL_USER", "sculostandfound@gmail.com"
)
EMAIL_HOST_PASSWORD = os.environ.get("CAMPUS_EMAIL_PASSWORD", "")
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = f"Campus Lost and Found <{EMAIL_HOST_USER}>"

if email_mode == "smtp" and (
    not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD
):
    raise ImproperlyConfigured(
        "SMTP email requires CAMPUS_EMAIL_USER and CAMPUS_EMAIL_PASSWORD."
    )

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
