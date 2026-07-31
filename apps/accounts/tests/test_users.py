from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class UserManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin_dsi",
            email="admin@topnet.tn",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.viewer = User.objects.create_user(
            username="lecteur",
            email="lecteur@topnet.tn",
            password="Secret123!",
            role=User.Role.VIEWER,
        )

    def test_list_users_requires_auth(self):
        response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/auth/users/",
            {
                "username": "manager1",
                "email": "manager1@topnet.tn",
                "password": "Secret123!",
                "role": "manager",
                "department": "DSI",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="manager1").exists())

    def test_viewer_cannot_list_users(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_endpoint(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "admin_dsi")


class UserManagementWebTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="webadmin",
            email="webadmin@topnet.tn",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_login_page_renders(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Topnet APM")

    def test_user_list_requires_login(self):
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 302)

    def test_admin_can_open_user_list(self):
        self.client.login(username="webadmin", password="Secret123!")
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion des utilisateurs")


class PasswordResetWebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetme",
            email="resetme@topnet.tn",
            password="Secret123!",
            role=User.Role.VIEWER,
        )

    def test_password_reset_page_renders(self):
        response = self.client.get("/password-reset/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mot de passe oublié")

    def test_password_reset_sends_email(self):
        from django.core import mail

        response = self.client.post("/password-reset/", {"email": "resetme@topnet.tn"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Réinitialisation", mail.outbox[0].subject)
        self.assertIn("resetme", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        self.assertIn("cid:topnet-logo", mail.outbox[0].alternatives[0].content)
        logo = next(
            attachment
            for attachment in mail.outbox[0].attachments
            if attachment.get("Content-ID") == "<topnet-logo>"
        )
        self.assertEqual(logo.get_content_type(), "image/png")

    def test_login_contains_forgot_password_link(self):
        response = self.client.get("/login/")
        self.assertContains(response, "/password-reset/")
