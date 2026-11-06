from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower


def validate_scu_email(value):
    if value.rsplit("@", 1)[-1].lower() != "scu.edu":
        raise ValidationError("Use an email address ending in @scu.edu.")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("An SCU email address is required.")

        if not full_name or not full_name.strip():
            raise ValueError("A full name is required.")

        user = self.model(
            email=email.strip().lower(),
            full_name=full_name.strip(),
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", True)

        for field in (
            "is_staff",
            "is_superuser",
            "is_active",
            "email_verified",
        ):
            if extra_fields.get(field) is not True:
                raise ValueError(f"A superuser must have {field}=True.")

        if not password:
            raise ValueError("A superuser must have a password.")

        return self.create_user(
            email=email,
            full_name=full_name,
            password=password,
            **extra_fields,
        )


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    id = models.BigAutoField(primary_key=True)

    email = models.EmailField(
        unique=True,
        validators=[validate_scu_email],
    )
    full_name = models.CharField(max_length=150)
    profile_picture = models.URLField(max_length=500, blank=True, default="")

    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_case_insensitive_unique",
            ),
        ]

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()
        self.full_name = self.full_name.strip()

        if not self.full_name:
            raise ValidationError({"full_name": "A full name is required."})

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else ""

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


from django.conf import settings
from django.utils import timezone


class EmailVerification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )
    code_hash = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    window_started_at = models.DateTimeField(default=timezone.now)
    send_count = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)


class PasswordResetCode(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_code",
    )
    code_hash = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    window_started_at = models.DateTimeField(default=timezone.now)
    send_count = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)
