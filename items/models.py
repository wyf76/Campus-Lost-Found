
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
        SCDI = "scdi", "Sobrato Campus for Discovery and Innovation (SCDI)"
        BERGIN_HALL = "bergin_hall", "Bergin Hall"
        HEAFEY_HALL = "heafey_hall", "Heafey Hall"
        ALUMNI_SCIENCE_HALL = "alumni_science_hall", "Alumni Science Hall"
        DALY_SCIENCE_CENTER = "daly_science_center", "Daly Science Center"
        OCONNOR_HALL = "oconnor_hall", "O'Connor Hall"
        KENNA_HALL = "kenna_hall", "Kenna Hall"
        VARI_HALL = "vari_hall", "Vari Hall"
        LUCAS_HALL = "lucas_hall", "Lucas Hall"
        LOYOLA_HALL = "loyola_hall", "Loyola Hall"
        ALAMEDA_HALL = "alameda_hall", "Alameda Hall"
        DOWD_ART_BUILDING = (
            "dowd_art_building",
            "Edward M. Dowd Art and Art History Building",
        )
        MALLEY_CENTER = "malley_center", "Malley Center"
        ORRADRE_LIBRARY = "orradre_library", "Orradre Library"
        OTHER = "other", "Other"

    item_type = models.CharField(max_length=5, choices=ItemType.choices)
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Category.choices)
    happened_on = models.DateField()
    happened_time = models.TimeField(blank=True, null=True)
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


class SavedReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "report"), name="items_unique_saved_report",
            ),
        ]


class ReportFlag(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("report", "reporter"), name="items_unique_report_flag",
            ),
        ]
