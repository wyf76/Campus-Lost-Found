# Convert Python data to JSON when simulating API requests.
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ReportForm
from .models import Report



User = get_user_model()


# Create an active, verified user for the tests.
def create_user(email="student@scu.edu", full_name="Test Student"):
    return User.objects.create_user(
        email=email,
        full_name=full_name,
        password="test-password-123",
        is_active=True,
        email_verified=True,
    )


# Create a report with default valid data
def create_report(author, **overrides):
    values = {
        "item_type": "lost",
        "title": "Blue backpack",
        "category": "bags",
        "happened_on": "2026-10-25",
        "location": "learning_commons",
        "location_details": "Near the front desk",
        "description": "A blue backpack with a notebook inside.",
        "author": author,
    }
    values.update(overrides)  # Replace defaults with any supplied values.
    return Report.objects.create(**values)  # Save and return the report.


# Test validation rules for the report form.
class ReportFormTests(TestCase):
    def setUp(self):
        # Provide valid report data for each form test.
        self.data = {
            "item_type": "lost",
            "title": "Blue backpack",
            "category": "bags",
            "happened_on": "2026-10-25",
            "location": "learning_commons",
            "location_details": "",
            "description": "A blue backpack with a notebook inside.",
        }

    def test_accepts_valid_report_fields(self):
        form = ReportForm(data=self.data)

        # Valid report data should pass form validation.
        self.assertTrue(form.is_valid(), form.errors)

    def test_accepts_title_at_maximum_length(self):
        # Test a title at the 100-character limit.
        data = {**self.data, "title": "x" * 100}

        self.assertTrue(ReportForm(data=data).is_valid())

    def test_rejects_title_over_maximum_length(self):
        # Test a title that exceeds the 100-character limit.
        data = {**self.data, "title": "x" * 101}
        form = ReportForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_rejects_none_for_required_title(self):
        # A required title cannot be None.
        data = {**self.data, "title": None}
        form = ReportForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_rejects_invalid_choice_and_date_values(self):
        # Test invalid item type, category, and date values.
        for field, value in (
            ("item_type", "missing"),
            ("category", "not-a-category"),
            ("happened_on", "not-a-date"),
        ):
            with self.subTest(field=field):
                data = {**self.data, field: value}
                self.assertFalse(ReportForm(data=data).is_valid())

    def test_accepts_all_scdi_building_locations(self):
        # These locations were added for the SCDI campus area.
        new_locations = {
            Report.Location.SCDI,
            Report.Location.BERGIN_HALL,
            Report.Location.HEAFEY_HALL,
            Report.Location.ALUMNI_SCIENCE_HALL,
            Report.Location.DALY_SCIENCE_CENTER,
            Report.Location.OCONNOR_HALL,
            Report.Location.KENNA_HALL,
            Report.Location.VARI_HALL,
            Report.Location.LUCAS_HALL,
            Report.Location.LOYOLA_HALL,
            Report.Location.ALAMEDA_HALL,
            Report.Location.DOWD_ART_BUILDING,
        }

        for location in new_locations:
            with self.subTest(location=location):
                data = {**self.data, "location": location}
                self.assertTrue(ReportForm(data=data).is_valid())

    def test_rejects_unlisted_location(self):
        # A location that is not one of the configured choices must be rejected.
        data = {**self.data, "location": "not-a-campus-building"}

        self.assertFalse(ReportForm(data=data).is_valid())


# Test default values and behavior of the Report model.
class ReportModelTests(TestCase):
    def setUp(self):
        # Create a report author for each model test.
        self.user = create_user()

    def test_new_report_defaults_to_unresolved(self):
        report = create_report(self.user)

        # A new report should not be marked as resolved.
        self.assertFalse(report.is_resolved)

    def test_created_at_is_set_when_report_is_saved(self):
        report = create_report(self.user)

        # The creation timestamp should be set automatically.
        self.assertIsNotNone(report.created_at)

    def test_author_reverse_relation_returns_report(self):
        report = create_report(self.user)

        # The author's reverse relation should return this report.
        self.assertEqual(self.user.reports.get(), report)

    def test_string_representation_includes_type_and_title(self):
        report = create_report(self.user)

        # Check the text returned by the model's __str__ method.
        self.assertEqual(str(report), "Lost: Blue backpack")

    def test_image_is_optional(self):
        report = create_report(self.user)

        # A report can be saved without an image.
        self.assertFalse(report.image)


# Test the API for creating reports.
class ReportApiTests(TestCase):
    def setUp(self):
        # Prepare a user, the API URL, and valid report data.
        self.user = create_user()
        self.url = reverse("items:report-list-create")
        self.payload = {
            "item_type": "lost",
            "title": "Blue backpack",
            "category": "bags",
            "happened_on": "2026-10-25",
            "location": "learning_commons",
            "location_details": "",
            "description": "A blue backpack with a notebook inside.",
        }

    def post_json(self, payload):
        # Simulate a POST request with a JSON request body.
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_anonymous_user_cannot_create_report(self):
        # Send a create request without logging in.
        response = self.post_json(self.payload)

        self.assertEqual(response.status_code, 401)  # Login is required.
        self.assertEqual(Report.objects.count(), 0)  # No report should be saved.

    def test_logged_in_user_creates_report_as_author(self):
        self.client.force_login(self.user)  # Simulate logging in as this user.

        response = self.post_json(self.payload)

        self.assertEqual(response.status_code, 201)  # The report was created.
        report = Report.objects.get()
        self.assertEqual(report.author, self.user)  # The logged-in user is the author.
        self.assertEqual(response.json()["report"]["author"]["id"], self.user.pk)

    def test_rejects_array_and_none_json_values(self):
        self.client.force_login(self.user)

        # Collect responses for requests whose top-level JSON value is an array.
        array_responses = []
        for payloads in ([self.payload], [self.payload] * 1000):
            with self.subTest(array_length=len(payloads)):
                array_responses.append(
                    self.client.post(
                        self.url,
                        data=json.dumps(payloads),
                        content_type="application/json",
                    )
                )

        # Test a null title and a numeric title.
        none_response = self.post_json({**self.payload, "title": None})
        wrong_type_response = self.post_json({**self.payload, "title": 123})

        # All array requests and invalid title values should be rejected.
        self.assertTrue(
            all(response.status_code == 400 for response in array_responses)
        )
        self.assertEqual(none_response.status_code, 400)
        self.assertEqual(wrong_type_response.status_code, 400)
        self.assertEqual(Report.objects.count(), 0)  # Invalid requests save nothing.

    def test_rejects_client_supplied_author(self):
        self.client.force_login(self.user)

        # The client must not choose the report author in the request body.
        response = self.post_json({**self.payload, "author": self.user.pk})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Report.objects.count(), 0)

    def test_title_length_boundary_is_enforced_by_api(self):
        self.client.force_login(self.user)

        # A title at the limit should be accepted; one character over should fail.
        valid_response = self.post_json({**self.payload, "title": "x" * 100})
        invalid_response = self.post_json({**self.payload, "title": "x" * 101})

        self.assertEqual(valid_response.status_code, 201)
        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(Report.objects.count(), 1)  # Only the valid request is saved.


# Test report listing, searching, filtering, and detail retrieval.
class ReportReadApiTests(TestCase):
    def setUp(self):
        # Create a report author and get the report-list API URL.
        self.user = create_user()
        self.list_url = reverse("items:report-list-create")

    def test_empty_report_list_returns_empty_array(self):
        # Request the list when the test database has no reports.
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reports"], [])

    def test_keyword_search_returns_only_matching_report(self):
        # Create one matching report and one report that should not match.
        match = create_report(self.user, title="Lost silver keys")
        create_report(self.user, title="Red scarf", category="clothing")

        # Search for "silver" using the q query parameter.
        response = self.client.get(self.list_url, {"q": "silver"})

        self.assertEqual(response.status_code, 200)
        # Only the matching report's ID should be returned.
        self.assertEqual(
            [report["id"] for report in response.json()["reports"]],
            [match.pk],
        )

    def test_combined_type_category_and_location_filters_return_single_match(self):
        # Create a report that matches all three filters.
        match = create_report(self.user)

        # Create a report that does not match those filters.
        create_report(
            self.user,
            item_type="found",
            title="Found keys",
            category="keys",
            location="scdi",
        )

        # Apply type, category, and location filters together.
        response = self.client.get(
            self.list_url,
            {
                "type": "lost",
                "category": "bags",
                "location": "learning_commons",
            },
        )

        self.assertEqual(response.status_code, 200)
        # Only the report matching every filter should be returned.
        self.assertEqual(
            [report["id"] for report in response.json()["reports"]],
            [match.pk],
        )

    def test_detail_returns_report_and_missing_id_returns_404(self):
        report = create_report(self.user)

        # Build the detail URL for an existing report and request it.
        detail_url = reverse("items:report-detail", args=[report.pk])
        response = self.client.get(detail_url)

        # Request a report ID that does not exist.
        missing_response = self.client.get(
            reverse("items:report-detail", args=[999999])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["report"]["id"], report.pk)
        self.assertEqual(missing_response.status_code, 404)

    def test_detail_includes_chat_start_url(self):
        report = create_report(self.user)
        detail_url = reverse("items:report-detail", args=[report.pk])

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["report"]["chat_start_url"],
            f"http://testserver/api/reports/{report.pk}/conversations/",
        )

    def test_invalid_or_unsupported_filter_returns_400(self):
        # "unknown" is not a valid report type.
        invalid_choice = self.client.get(self.list_url, {"type": "unknown"})

        # "author" is not a supported list-filter parameter.
        unsupported = self.client.get(self.list_url, {"author": "1"})

        self.assertEqual(invalid_choice.status_code, 400)
        self.assertEqual(unsupported.status_code, 400)
