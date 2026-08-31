from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase, TestCase

from apps.accounts.roles import (
    can_configure_platform,
    can_manage_users,
    can_read,
    can_read_infrastructure,
    can_read_patrimoine,
    can_write_infrastructure,
    can_write_patrimoine,
    can_write_users,
    is_admin_dsi,
    is_admin_system,
    is_platform_admin,
)

User = get_user_model()


class RoleHelpersUnitTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="role_admin", password="Secret123!", role=User.Role.ADMIN
        )
        self.dsi = User.objects.create_user(
            username="role_dsi", password="Secret123!", role=User.Role.DSI
        )
        self.system = User.objects.create_user(
            username="role_system", password="Secret123!", role=User.Role.SYSTEM
        )

    def test_platform_admin_users_only(self):
        self.assertTrue(is_platform_admin(self.admin))
        self.assertFalse(is_platform_admin(self.dsi))
        self.assertTrue(can_manage_users(self.admin))
        self.assertTrue(can_write_users(self.admin))
        self.assertFalse(can_manage_users(self.dsi))
        self.assertFalse(can_write_users(self.dsi))

    def test_admin_dsi_patrimoine_without_users(self):
        self.assertTrue(is_admin_dsi(self.dsi))
        self.assertFalse(is_admin_dsi(self.admin))
        self.assertTrue(can_write_patrimoine(self.dsi))
        self.assertTrue(can_configure_platform(self.dsi))
        self.assertFalse(can_write_patrimoine(self.admin))
        self.assertFalse(can_configure_platform(self.admin))

    def test_admin_system_infrastructure_only(self):
        self.assertTrue(is_admin_system(self.system))
        self.assertTrue(can_read_infrastructure(self.system))
        self.assertTrue(can_write_infrastructure(self.system))
        self.assertFalse(can_read_patrimoine(self.system))
        self.assertFalse(can_write_patrimoine(self.system))
        self.assertFalse(can_manage_users(self.system))

    def test_can_read_any_section(self):
        self.assertTrue(can_read(self.admin))
        self.assertTrue(can_read(self.dsi))
        self.assertTrue(can_read(self.system))


class AnonymousRoleHelpersTests(SimpleTestCase):
    def test_anonymous_denied(self):
        anon = AnonymousUser()
        self.assertFalse(is_platform_admin(anon))
        self.assertFalse(is_admin_dsi(anon))
        self.assertFalse(is_admin_system(anon))
        self.assertFalse(can_manage_users(anon))
        self.assertFalse(can_write_users(anon))
        self.assertFalse(can_write_patrimoine(anon))
        self.assertFalse(can_write_infrastructure(anon))
        self.assertFalse(can_configure_platform(anon))
        self.assertFalse(can_read(anon))
