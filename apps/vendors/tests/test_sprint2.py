from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.certificates.models import Certificate
from apps.contracts.models import Contract
from apps.domains.models import Domain
from apps.vendors.models import Vendor

User = get_user_model()


class Sprint2APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="s2mgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.client.force_authenticate(self.manager)
        self.app = Application.objects.create(name="CRM Sprint2")

    def test_vendor_create(self):
        response = self.client.post(
            "/api/vendors/",
            {
                "name": "OVHcloud",
                "vendor_type": "hosting",
                "contact_email": "support@ovh.example",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Vendor.objects.filter(name="OVHcloud").exists())

    def test_contract_create(self):
        vendor = Vendor.objects.create(name="DigiCert Vendor", vendor_type="security")
        response = self.client.post(
            "/api/contracts/",
            {
                "reference": "CTR-2026-001",
                "title": "Support CRM",
                "vendor": vendor.pk,
                "application": self.app.pk,
                "contract_type": "support",
                "status": "active",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "currency": "TND",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Contract.objects.filter(reference="CTR-2026-001").exists())

    def test_domain_create(self):
        response = self.client.post(
            "/api/domains/",
            {
                "fqdn": "crm.topnet.tn",
                "registrar": "OVH",
                "status": "active",
                "application": self.app.pk,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Domain.objects.filter(fqdn="crm.topnet.tn").exists())

    def test_certificate_create(self):
        domain = Domain.objects.create(fqdn="secure.topnet.tn", status="active")
        response = self.client.post(
            "/api/certificates/",
            {
                "common_name": "secure.topnet.tn",
                "certificate_type": "single",
                "status": "valid",
                "issuer": "Let's Encrypt",
                "domain": domain.pk,
                "application": self.app.pk,
                "expires_at": (date.today() + timedelta(days=90)).isoformat(),
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Certificate.objects.filter(common_name="secure.topnet.tn").exists())


class Sprint2WebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="s2web",
            password="Secret123!",
            role=User.Role.MANAGER,
        )

    def test_list_pages_require_login_then_render(self):
        for url in ("/vendors/", "/contracts/", "/domains/", "/certificates/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
        self.client.login(username="s2web", password="Secret123!")
        for url, title in (
            ("/vendors/", "Fournisseurs"),
            ("/contracts/", "Contrats"),
            ("/domains/", "Domaines"),
            ("/certificates/", "Certificats"),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, title)
