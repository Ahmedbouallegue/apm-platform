from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.environments.models import Environment

User = get_user_model()


class EnvironmentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="envmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.app = Application.objects.create(
            name="Portail RH",
            status=Application.Status.PRODUCTION,
            criticality=Application.Criticality.HIGH,
        )

    def test_create_prod_environment(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/environments/",
            {
                "application": self.app.pk,
                "name": "Production",
                "env_type": "prod",
                "url": "https://rh.topnet.tn",
                "ip_address": "10.10.1.20",
                "os": "Linux",
                "cpu": "8 vCPU",
                "ram": "16 Go",
                "hosting_provider": "On-premise",
                "docker": True,
                "kubernetes": False,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(
            Environment.objects.filter(application=self.app, env_type="prod").exists()
        )

    def test_unique_env_type_per_application(self):
        Environment.objects.create(
            application=self.app,
            name="DEV",
            env_type=Environment.EnvType.DEV,
        )
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/environments/",
            {
                "application": self.app.pk,
                "name": "DEV 2",
                "env_type": "dev",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EnvironmentWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webenv",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.app = Application.objects.create(name="Billing")
        Environment.objects.create(
            application=self.app,
            name="RECETTE",
            env_type=Environment.EnvType.RECETTE,
            url="https://recette.billing.local",
        )

    def test_list_page(self):
        self.client.login(username="webenv", password="Secret123!")
        response = self.client.get("/environments/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion des environnements")
        self.assertContains(response, "Billing")
