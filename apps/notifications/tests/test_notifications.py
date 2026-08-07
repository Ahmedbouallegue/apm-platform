from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.certificates.models import Certificate
from apps.notifications.models import Notification
from apps.notifications.tasks import check_expiring_resources

User = get_user_model()


class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="notmgr", password="Secret123!", role=User.Role.MANAGER
        )

    def test_list_own_notifications(self):
        Notification.objects.create(
            user=self.manager,
            title="Alerte test",
            message="Message",
            notification_type=Notification.NotificationType.ALERT,
        )
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)


class ExpiryTaskTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="dsiuser", password="Secret123!", role=User.Role.DSI
        )
        Certificate.objects.create(
            common_name="expiring.topnet.tn",
            expires_at=timezone.localdate() + timedelta(days=10),
            status=Certificate.Status.VALID,
        )

    def test_check_expiring_resources_creates_notifications(self):
        result = check_expiring_resources()
        self.assertIn(30, result["thresholds"])
        self.assertIn(60, result["thresholds"])
        self.assertIn(0, result["thresholds"])
        self.assertGreaterEqual(result["created"]["certificates"], 1)
        self.assertTrue(
            Notification.objects.filter(notification_type=Notification.NotificationType.EXPIRY).exists()
        )
        notif = Notification.objects.filter(
            notification_type=Notification.NotificationType.EXPIRY
        ).first()
        self.assertIn("seuil=30", notif.link)

    def test_check_expiring_resources_deduplicates(self):
        first = check_expiring_resources()
        second = check_expiring_resources()
        self.assertGreaterEqual(first["created"]["certificates"], 1)
        self.assertEqual(second["created"]["certificates"], 0)
        self.assertGreaterEqual(second["skipped"]["certificates"], 1)
        self.assertEqual(
            Notification.objects.filter(
                notification_type=Notification.NotificationType.EXPIRY
            ).count(),
            1,
        )

    def test_j60_threshold_for_far_expiry(self):
        Certificate.objects.create(
            common_name="far.topnet.tn",
            expires_at=timezone.localdate() + timedelta(days=45),
            status=Certificate.Status.VALID,
        )
        result = check_expiring_resources()
        self.assertGreaterEqual(result["created"]["certificates"], 2)
        self.assertTrue(
            Notification.objects.filter(link__contains="seuil=60").exists()
        )


class RoleAccessWebTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="roleadmin",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            username="rolemanager",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.viewer = User.objects.create_user(
            username="roleviewer",
            password="Secret123!",
            role=User.Role.VIEWER,
        )

    def test_admin_can_open_settings(self):
        self.client.login(username="roleadmin", password="Secret123!")
        response = self.client.get("/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paramètres globaux")

    def test_manager_cannot_open_settings(self):
        self.client.login(username="rolemanager", password="Secret123!")
        response = self.client.get("/settings/")
        self.assertEqual(response.status_code, 302)

    def test_manager_can_list_users_but_not_create(self):
        self.client.login(username="rolemanager", password="Secret123!")
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Nouvel utilisateur")
        create = self.client.get("/users/new/")
        self.assertEqual(create.status_code, 302)

    def test_viewer_cannot_list_users(self):
        self.client.login(username="roleviewer", password="Secret123!")
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 302)


class LoginNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loguser",
            password="Secret123!",
            role=User.Role.MANAGER,
            first_name="Sara",
            last_name="Ben",
        )

    def test_password_login_creates_system_notification_and_toast(self):
        response = self.client.post(
            "/login/",
            {"username": "loguser", "password": "Secret123!"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                notification_type=Notification.NotificationType.SYSTEM,
                title="Connexion réussie",
            ).exists()
        )
        self.assertContains(response, "Bienvenue")

    def test_login_notification_once_per_day(self):
        from apps.notifications.services.notifications import notify_user_login

        first = notify_user_login(user=self.user, method="password")
        second = notify_user_login(user=self.user, method="password")
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(
            Notification.objects.filter(
                user=self.user, notification_type=Notification.NotificationType.SYSTEM
            ).count(),
            1,
        )


class NotificationWebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="webnot", password="Secret123!", role=User.Role.MANAGER
        )
        Notification.objects.create(
            user=self.user, title="Notif web", message="Hello", notification_type="info"
        )

    def test_list_page(self):
        self.client.login(username="webnot", password="Secret123!")
        response = self.client.get("/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notif web")

    def test_sidebar_badge(self):
        Notification.objects.create(
            user=self.user,
            title="Non lue",
            message="x",
            notification_type="info",
            status=Notification.Status.UNREAD,
        )
        self.client.login(username="webnot", password="Secret123!")
        response = self.client.get("/")
        self.assertContains(response, "nav-badge")
