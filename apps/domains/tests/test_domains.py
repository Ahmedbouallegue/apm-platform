from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.domains.models import Domain

User = get_user_model()


class DomainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="dommgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )

    def test_create_domain(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/domains/",
            {
                "fqdn": "app.topnet.tn",
                "registrar": "OVH",
                "dns_provider": "Cloudflare",
                "status": "active",
                "expires_at": (date.today() + timedelta(days=365)).isoformat(),
                "is_primary": True,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Domain.objects.filter(fqdn="app.topnet.tn").exists())


class DomainWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webdom",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Domain.objects.create(fqdn="portal.topnet.tn", status=Domain.Status.ACTIVE)

    def test_list_page(self):
        self.client.login(username="webdom", password="Secret123!")
        response = self.client.get("/domains/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Noms de domaine")
        self.assertContains(response, "portal.topnet.tn")
