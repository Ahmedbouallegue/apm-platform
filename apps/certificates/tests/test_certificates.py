from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.certificates.models import Certificate

User = get_user_model()


class CertificateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="certmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )

    def test_create_certificate(self):
        self.client.force_authenticate(self.manager)
        expires = (date.today() + timedelta(days=90)).isoformat()
        response = self.client.post(
            "/api/certificates/",
            {
                "common_name": "*.topnet.tn",
                "issuer": "Let's Encrypt",
                "certificate_type": "wildcard",
                "status": "valid",
                "expires_at": expires,
                "auto_renew": True,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Certificate.objects.filter(common_name="*.topnet.tn").exists())

    def test_soft_delete_certificate(self):
        cert = Certificate.objects.create(
            common_name="api.topnet.tn",
            expires_at=date.today() + timedelta(days=30),
        )
        self.client.force_authenticate(self.manager)
        response = self.client.delete(f"/api/certificates/{cert.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        cert.refresh_from_db()
        self.assertTrue(cert.is_deleted)


class CertificateWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webcert",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Certificate.objects.create(
            common_name="www.topnet.tn",
            expires_at=date.today() + timedelta(days=60),
            status=Certificate.Status.VALID,
        )

    def test_list_page(self):
        self.client.login(username="webcert", password="Secret123!")
        response = self.client.get("/certificates/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certificats SSL")
        self.assertContains(response, "www.topnet.tn")
