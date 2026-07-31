from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.environments.models import Environment
from apps.servers.models import Server

User = get_user_model()


class ServerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="srvmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )

    def test_create_server(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/servers/",
            {
                "name": "srv-app-01",
                "ip_address": "10.20.1.10",
                "os": "Ubuntu 22.04",
                "cpu": "8 vCPU",
                "ram": "32 Go",
                "datacenter": "DC Tunis",
                "server_type": "vm",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Server.objects.filter(name="srv-app-01").exists())

    def test_link_environment_to_server(self):
        server = Server.objects.create(
            name="srv-prod-01",
            ip_address="10.20.1.20",
            server_type=Server.ServerType.PHYSICAL,
        )
        app = Application.objects.create(name="CRM")
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/environments/",
            {
                "application": app.pk,
                "server": server.pk,
                "name": "PROD",
                "env_type": "prod",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        env = Environment.objects.get(application=app, env_type="prod")
        self.assertEqual(env.server_id, server.pk)


class ServerWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="websrv",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Server.objects.create(
            name="srv-web-01",
            ip_address="10.1.1.5",
            server_type=Server.ServerType.CLOUD,
            datacenter="Azure North Africa",
        )

    def test_list_page(self):
        self.client.login(username="websrv", password="Secret123!")
        response = self.client.get("/servers/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion des serveurs")
        self.assertContains(response, "srv-web-01")
