"""Tests durcissement sécurité."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.documents.models import Document

User = get_user_model()


class SecureMediaTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="sec_viewer",
            password="Secret123!",
            role=User.Role.VIEWER,
        )
        self.admin = User.objects.create_user(
            username="sec_admin",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        upload = SimpleUploadedFile("note.txt", b"confidentiel", content_type="text/plain")
        self.document = Document.objects.create(title="Note interne", file=upload)

    def test_anonymous_cannot_download_media(self):
        url = self.document.file.url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_viewer_can_download_media(self):
        self.client.login(username="sec_viewer", password="Secret123!")
        response = self.client.get(self.document.file.url)
        self.assertEqual(response.status_code, 200)
        body = b"".join(response.streaming_content)
        self.assertIn(b"confidentiel", body)

    def test_path_traversal_blocked(self):
        self.client.login(username="sec_viewer", password="Secret123!")
        response = self.client.get("/media/../manage.py")
        self.assertIn(response.status_code, {403, 404})


class ApiDocsProtectionTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="sec_doc_viewer",
            password="Secret123!",
            role=User.Role.VIEWER,
        )
        self.admin = User.objects.create_user(
            username="sec_doc_admin",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_anonymous_cannot_open_swagger(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 302)

    def test_viewer_cannot_open_swagger(self):
        self.client.login(username="sec_doc_viewer", password="Secret123!")
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_open_swagger(self):
        self.client.login(username="sec_doc_admin", password="Secret123!")
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)


class AdminAccessTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="sec_mgr",
            password="Secret123!",
            role=User.Role.MANAGER,
            is_staff=True,
        )
        self.admin = User.objects.create_user(
            username="sec_adm",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_manager_staff_blocked_from_admin(self):
        self.client.login(username="sec_mgr", password="Secret123!")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 403)

    def test_admin_dsi_can_access_admin(self):
        self.client.login(username="sec_adm", password="Secret123!")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)


@override_settings(LOGIN_RATE_LIMIT_ENABLED=True, LOGIN_RATE_LIMIT_MAX_ATTEMPTS=3)
class LoginRateLimitTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="rate_user",
            password="Secret123!",
            role=User.Role.VIEWER,
        )

    def test_web_login_rate_limited_after_failures(self):
        for _ in range(3):
            self.client.post(
                reverse("web:login"),
                {"username": "rate_user", "password": "wrong"},
            )
        response = self.client.post(
            reverse("web:login"),
            {"username": "rate_user", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 429)


class DocumentUploadValidationTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="sec_uploader",
            password="Secret123!",
            role=User.Role.MANAGER,
        )

    def test_rejects_executable_upload(self):
        self.client.login(username="sec_uploader", password="Secret123!")
        bad = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")
        response = self.client.post(
            reverse("documents:create"),
            {
                "title": "Bad file",
                "category": Document.Category.ARCHITECTURE,
                "file": bad,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "non autoris")
