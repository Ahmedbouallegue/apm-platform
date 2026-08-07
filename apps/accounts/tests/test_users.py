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
        self.assertContains(response, "Exporter CSV")
        self.assertContains(response, "Importer CSV")

    def test_export_csv(self):
        self.client.login(username="webadmin", password="Secret123!")
        response = self.client.get("/users/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        body = response.content.decode("utf-8")
        self.assertIn("username,email,first_name", body)
        self.assertIn("webadmin", body)

    def test_import_csv_creates_user(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username="webadmin", password="Secret123!")
        csv_data = (
            "username,email,first_name,last_name,role,phone,department,is_active,password\n"
            "csvuser,csvuser@topnet.tn,Csv,User,viewer,,DSI,1,Secret123!\n"
        )
        uploaded = SimpleUploadedFile(
            "users.csv",
            csv_data.encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post("/users/import/", {"file": uploaded})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="csvuser")
        self.assertEqual(user.email, "csvuser@topnet.tn")
        self.assertEqual(user.role, User.Role.VIEWER)
        self.assertTrue(user.check_password("Secret123!"))

    def test_import_csv_updates_existing(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        User.objects.create_user(
            username="csvupd",
            email="old@topnet.tn",
            password="Secret123!",
            role=User.Role.VIEWER,
        )
        self.client.login(username="webadmin", password="Secret123!")
        csv_data = (
            "username,email,first_name,last_name,role,phone,department,is_active,password\n"
            "csvupd,new@topnet.tn,New,Name,manager,,Ops,1,\n"
        )
        uploaded = SimpleUploadedFile(
            "users.csv",
            csv_data.encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post("/users/import/", {"file": uploaded})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="csvupd")
        self.assertEqual(user.email, "new@topnet.tn")
        self.assertEqual(user.role, User.Role.MANAGER)
        self.assertEqual(user.first_name, "New")

    def test_viewer_cannot_export_csv(self):
        User.objects.create_user(
            username="webviewer",
            email="webviewer@topnet.tn",
            password="Secret123!",
            role=User.Role.VIEWER,
        )
        self.client.login(username="webviewer", password="Secret123!")
        response = self.client.get("/users/export.csv")
        self.assertEqual(response.status_code, 302)


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
