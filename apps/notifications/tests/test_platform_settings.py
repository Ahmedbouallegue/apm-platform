from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import PlatformSettings

User = get_user_model()


class PlatformSettingsUnitTests(TestCase):
    def test_load_singleton_and_thresholds(self):
        settings_obj = PlatformSettings.load()
        self.assertEqual(settings_obj.pk, 1)
        self.assertEqual(settings_obj.thresholds(), [0, 30, 60])

        settings_obj.alert_on_expiry = False
        settings_obj.alert_days_60 = 45
        settings_obj.alert_days_30 = 15
        settings_obj.save()
        self.assertEqual(PlatformSettings.load().thresholds(), [15, 45])


class PlatformSettingsWebTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="setadmin",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_admin_can_update_settings(self):
        self.client.login(username="setadmin", password="Secret123!")
        response = self.client.post(
            "/settings/",
            {
                "alert_days_60": 50,
                "alert_days_30": 20,
                "alert_on_expiry": "on",
                "alert_cooldown_days": 5,
            },
        )
        self.assertEqual(response.status_code, 302)
        settings_obj = PlatformSettings.load()
        self.assertEqual(settings_obj.alert_days_60, 50)
        self.assertEqual(settings_obj.alert_days_30, 20)
        self.assertEqual(settings_obj.alert_cooldown_days, 5)
        self.assertTrue(settings_obj.alert_on_expiry)
