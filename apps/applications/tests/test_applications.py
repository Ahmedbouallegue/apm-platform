from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.technologies.models import Technology

User = get_user_model()


class ApplicationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="mgr",
            password="Secret123!",
            role=User.Role.MANAGER,
            email="mgr@topnet.tn",
        )
        self.viewer = User.objects.create_user(
            username="view",
            password="Secret123!",
            role=User.Role.VIEWER,
            email="view@topnet.tn",
        )
        self.tech = Technology.objects.create(
            name="Django",
            tech_type=Technology.TechType.FRAMEWORK,
            version="5.2",
        )

    def test_manager_can_create_application(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/applications/",
            {
                "name": "Portail RH",
                "description": "Portail ressources humaines",
                "criticality": "high",
                "status": "production",
                "user_count": 1200,
                "business_unit": "RH",
                "owner": self.manager.pk,
                "technology_ids": [self.tech.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        app = Application.objects.get(name="Portail RH")
        self.assertEqual(app.technologies.count(), 1)

    def test_viewer_cannot_create(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            "/api/applications/",
            {"name": "X", "criticality": "low", "status": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ApplicationWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Application.objects.create(
            name="Billing",
            status=Application.Status.PRODUCTION,
            criticality=Application.Criticality.CRITICAL,
            business_unit="Finance",
            owner=self.manager,
        )

    def test_list_requires_login(self):
        response = self.client.get("/applications/")
        self.assertEqual(response.status_code, 302)

    def test_manager_sees_list(self):
        self.client.login(username="webmgr", password="Secret123!")
        response = self.client.get("/applications/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Billing")
        self.assertContains(response, "Gestion des applications")
