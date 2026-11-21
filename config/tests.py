from pathlib import Path
import re
from unittest import skipUnless

from django.conf import settings
from django.test import SimpleTestCase


FRONTEND_INDEX = Path(settings.BASE_DIR) / "dist" / "index.html"


@skipUnless(FRONTEND_INDEX.is_file(), "Run npm run build before testing the frontend.")
class FrontendServingTests(SimpleTestCase):
    def test_root_serves_the_react_app_shell(self):
        response = self.client.get("/", secure=not settings.DEBUG)
        page = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('<div id="root"></div>', page)
        assets = re.findall(r'(?:src|href)="(/static/assets/[^\"]+)"', page)
        self.assertTrue(assets, "The built page should reference Vite assets.")

        for asset_url in assets:
            with self.subTest(asset_url=asset_url):
                asset_response = self.client.get(asset_url, secure=not settings.DEBUG)
                self.assertEqual(asset_response.status_code, 200)

    def test_csrf_api_remains_available_beside_the_frontend(self):
        response = self.client.get("/api/auth/csrf/", secure=not settings.DEBUG)

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrfToken", response.json())
