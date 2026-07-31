from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.technologies.models import Technology

User = get_user_model()


class TechnologyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="techmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.viewer = User.objects.create_user(
            username="techview",
            password="Secret123!",
            role=User.Role.VIEWER,
        )

    def test_manager_can_create(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/technologies/",
            {
                "name": "PostgreSQL",
                "tech_type": "database",
                "version": "16",
                "description": "SGBD principal",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Technology.objects.filter(name="PostgreSQL", version="16").exists())

    def test_viewer_cannot_create(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            "/api/technologies/",
            {"name": "Redis", "tech_type": "middleware"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TechnologyWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webtech",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Technology.objects.create(
            name="Django",
            tech_type=Technology.TechType.FRAMEWORK,
            version="5.2",
        )

    def test_list_page(self):
        self.client.login(username="webtech", password="Secret123!")
        response = self.client.get("/technologies/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion des technologies")
        self.assertContains(response, "Django")
