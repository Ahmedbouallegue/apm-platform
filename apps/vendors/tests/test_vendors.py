from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.vendors.models import Vendor

User = get_user_model()


class VendorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="vendmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )

    def test_create_vendor(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/vendors/",
            {
                "name": "Orange Business",
                "vendor_type": "telecom",
                "contact_name": "Service Support",
                "contact_email": "support@orange.tn",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Vendor.objects.filter(name="Orange Business").exists())


class VendorWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webvend",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Vendor.objects.create(name="DigiCert", vendor_type=Vendor.VendorType.SECURITY)

    def test_list_page(self):
        self.client.login(username="webvend", password="Secret123!")
        response = self.client.get("/vendors/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion des fournisseurs")
        self.assertContains(response, "DigiCert")
