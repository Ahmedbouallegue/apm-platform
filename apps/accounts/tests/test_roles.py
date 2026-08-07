from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase, TestCase

from apps.accounts.roles import (
    can_configure_platform,
    can_manage_users,
    can_read,
    can_write_patrimoine,
    can_write_users,
    is_admin_dsi,
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
        self.manager = User.objects.create_user(
            username="role_mgr", password="Secret123!", role=User.Role.MANAGER
        )
        self.viewer = User.objects.create_user(
            username="role_view", password="Secret123!", role=User.Role.VIEWER
        )

    def test_is_admin_dsi(self):
        self.assertTrue(is_admin_dsi(self.admin))
        self.assertTrue(is_admin_dsi(self.dsi))
        self.assertFalse(is_admin_dsi(self.manager))
        self.assertFalse(is_admin_dsi(self.viewer))

    def test_can_write_users_admin_only(self):
        self.assertTrue(can_write_users(self.admin))
        self.assertTrue(can_write_users(self.dsi))
        self.assertFalse(can_write_users(self.manager))
        self.assertFalse(can_write_users(self.viewer))

    def test_can_manage_users_includes_manager(self):
        self.assertTrue(can_manage_users(self.admin))
        self.assertTrue(can_manage_users(self.manager))
        self.assertFalse(can_manage_users(self.viewer))

    def test_can_write_patrimoine(self):
        self.assertTrue(can_write_patrimoine(self.manager))
        self.assertTrue(can_write_patrimoine(self.admin))
        self.assertFalse(can_write_patrimoine(self.viewer))

    def test_can_configure_platform(self):
        self.assertTrue(can_configure_platform(self.admin))
        self.assertFalse(can_configure_platform(self.manager))

    def test_can_read(self):
        self.assertTrue(can_read(self.viewer))
        self.assertTrue(can_read(self.manager))


class AnonymousRoleHelpersTests(SimpleTestCase):
    def test_anonymous_denied(self):
        anon = AnonymousUser()
        self.assertFalse(is_admin_dsi(anon))
        self.assertFalse(can_manage_users(anon))
        self.assertFalse(can_write_users(anon))
        self.assertFalse(can_write_patrimoine(anon))
        self.assertFalse(can_configure_platform(anon))
        self.assertFalse(can_read(anon))
