
from django.conf import settings
from django.db import models


class Report(models.Model):
    class ItemType(models.TextChoices):
        LOST = "lost", "Lost"
        FOUND = "found", "Found"

    class Category(models.TextChoices):
        ELECTRONICS = "electronics", "Electronics"
        BAGS = "bags", "Bags"
        KEYS = "keys", "Keys"
        CLOTHING = "clothing", "Clothing"
        BOOKS = "books", "Books"
        OTHER = "other", "Other"

    class Location(models.TextChoices):
        LEARNING_COMMONS = "learning_commons", "Learning Commons"
        BENSON_CENTER = "benson_center", "Benson Center"
        SCDI = "scdi", "SCDI"
        MALLEY_CENTER = "malley_center", "Malley Center"
        ORRADRE_LIBRARY = "orradre_library", "Orradre Library"
        OTHER = "other", "Other"

    item_type = models.CharField(max_length=5, choices=ItemType.choices)
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Category.choices)
    happened_on = models.DateField()
    location = models.CharField(max_length=40, choices=Location.choices)
    location_details = models.CharField(max_length=200, blank=True)
    description = models.TextField()

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports",
    )

    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(
        upload_to="report_images/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.title}"