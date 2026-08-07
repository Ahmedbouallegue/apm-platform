from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.servers.models import Server

User = get_user_model()


class ValidationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="valmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
            email="valmgr@topnet.tn",
        )
        self.client.force_authenticate(self.manager)

    def test_reject_weak_password_on_user_create(self):
        admin = User.objects.create_user(
            username="adminval",
            password="Secret123!",
            role=User.Role.ADMIN,
            email="adminval@topnet.tn",
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            "/api/auth/users/",
            {
                "username": "weakuser",
                "email": "weak@topnet.tn",
                "password": "password",
                "role": "viewer",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_invalid_application_dates(self):
        response = self.client.post(
            "/api/applications/",
            {
                "name": "App Dates",
                "criticality": "medium",
                "status": "project",
                "go_live_date": "2026-12-01",
                "end_of_life_date": "2026-01-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_of_life_date", response.data)

    def test_reject_duplicate_server_ip(self):
        Server.objects.create(name="srv-a", ip_address="10.9.9.9", server_type="vm")
        response = self.client.post(
            "/api/servers/",
            {"name": "srv-b", "ip_address": "10.9.9.9", "server_type": "vm"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_invalid_phone_web_form(self):
        User.objects.create_user(
            username="adminform",
            password="Secret123!",
            role=User.Role.ADMIN,
            email="adminform@topnet.tn",
        )
        self.client.logout()
        assert self.client.login(username="adminform", password="Secret123!")
        response = self.client.post(
            "/users/new/",
            {
                "username": "badphone",
                "email": "badphone@topnet.tn",
                "password1": "Secret123!",
                "password2": "Secret123!",
                "role": "viewer",
                "phone": "abc",
                "department": "DSI",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("phone", form.errors)
        self.assertFalse(User.objects.filter(username="badphone").exists())
