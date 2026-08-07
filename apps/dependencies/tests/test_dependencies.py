from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.dependencies.models import Dependency

User = get_user_model()


class DependencyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="depmgr", password="Secret123!", role=User.Role.MANAGER
        )
        self.src = Application.objects.create(name="Portail RH")
        self.tgt = Application.objects.create(name="API Paie")

    def test_create_dependency(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/dependencies/",
            {
                "dependency_type": "api",
                "description": "Appels REST paie",
                "source_application": self.src.pk,
                "target_application": self.tgt.pk,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Dependency.objects.count(), 1)


class DependencyWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webdep", password="Secret123!", role=User.Role.MANAGER
        )
        src = Application.objects.create(name="Intranet")
        Dependency.objects.create(
            source_application=src,
            target_external="Active Directory",
            dependency_type=Dependency.DependencyType.AUTH,
        )

    def test_list_page(self):
        self.client.login(username="webdep", password="Secret123!")
        response = self.client.get("/dependencies/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Active Directory")
