from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.domains.models import Domain
from apps.domains.services.domains import domain_create, domain_soft_delete, domain_update

User = get_user_model()


class DomainServiceUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="domsvc", password="Secret123!", role=User.Role.MANAGER
        )

    def test_create_with_auto_renew_and_soft_delete(self):
        domain = domain_create(
            data={
                "fqdn": "secure.topnet.tn",
                "status": Domain.Status.ACTIVE,
                "expires_at": date.today() + timedelta(days=200),
                "auto_renew": True,
                "is_primary": True,
            },
            user=self.user,
        )
        self.assertTrue(domain.auto_renew)
        self.assertTrue(
            AuditLog.objects.filter(
                action="create", entity="Domain", entity_id=str(domain.pk)
            ).exists()
        )

        domain_update(domain=domain, data={"auto_renew": False}, user=self.user)
        domain.refresh_from_db()
        self.assertFalse(domain.auto_renew)

        domain_soft_delete(domain=domain, user=self.user)
        domain.refresh_from_db()
        self.assertTrue(domain.is_deleted)


class DomainAutoRenewAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="domapi", password="Secret123!", role=User.Role.MANAGER
        )

    def test_create_domain_with_auto_renew(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/domains/",
            {
                "fqdn": "renew.topnet.tn",
                "status": "active",
                "expires_at": (date.today() + timedelta(days=365)).isoformat(),
                "auto_renew": True,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        domain = Domain.objects.get(fqdn="renew.topnet.tn")
        self.assertTrue(domain.auto_renew)
