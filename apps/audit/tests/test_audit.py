from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.services.audit import audit_log_create

User = get_user_model()


class AuditAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="audmgr", password="Secret123!", role=User.Role.MANAGER
        )
        audit_log_create(
            action="create",
            entity="Application",
            entity_id="1",
            details="Création test",
            user=self.manager,
        )

    def test_list_audit_logs(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        self.assertEqual(AuditLog.objects.count(), 1)


class AuditWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webaud", password="Secret123!", role=User.Role.MANAGER
        )
        audit_log_create(action="login", entity="User", entity_id="1", user=self.manager)

    def test_list_page(self):
        self.client.login(username="webaud", password="Secret123!")
        response = self.client.get("/audit/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "login")


class AuditCoverageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="audadmin",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_login_creates_audit_entry(self):
        self.client.post("/login/", {"username": "audadmin", "password": "Secret123!"})
        self.assertTrue(
            AuditLog.objects.filter(action="login", entity="User", user=self.admin).exists()
        )

    def test_application_create_is_audited(self):
        from apps.applications.services.applications import application_create

        app = application_create(
            data={
                "name": "Audit App",
                "description": "Test",
                "status": "production",
                "criticality": "medium",
            },
            user=self.admin,
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="create", entity="Application", entity_id=str(app.pk)
            ).exists()
        )

    def test_domain_auto_renew_field(self):
        from datetime import date

        from apps.domains.models import Domain

        domain = Domain.objects.create(
            fqdn="auto.topnet.tn",
            expires_at=date(2030, 1, 1),
            auto_renew=True,
        )
        self.assertTrue(domain.auto_renew)
