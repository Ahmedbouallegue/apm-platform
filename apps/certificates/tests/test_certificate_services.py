from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.audit.models import AuditLog
from apps.certificates.models import Certificate
from apps.certificates.services.certificates import (
    certificate_create,
    certificate_soft_delete,
    certificate_update,
)

User = get_user_model()


class CertificateServiceUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="certsvc", password="Secret123!", role=User.Role.MANAGER
        )

    def test_create_update_soft_delete(self):
        cert = certificate_create(
            data={
                "common_name": "api.topnet.tn",
                "issuer": "Let's Encrypt",
                "certificate_type": Certificate.CertificateType.SINGLE,
                "status": Certificate.Status.VALID,
                "expires_at": date.today() + timedelta(days=90),
                "auto_renew": True,
            },
            user=self.user,
        )
        self.assertTrue(cert.auto_renew)
        self.assertTrue(
            AuditLog.objects.filter(
                action="create", entity="Certificate", entity_id=str(cert.pk)
            ).exists()
        )

        certificate_update(
            certificate=cert,
            data={"issuer": "DigiCert"},
            user=self.user,
        )
        cert.refresh_from_db()
        self.assertEqual(cert.issuer, "DigiCert")

        certificate_soft_delete(certificate=cert, user=self.user)
        cert.refresh_from_db()
        self.assertTrue(cert.is_deleted)
