from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.applications.models import Application
from apps.applications.services.applications import (
    application_create,
    application_restore,
    application_soft_delete,
    application_update,
)
from apps.audit.models import AuditLog
from apps.technologies.models import Technology

User = get_user_model()


class ApplicationServiceUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="appsvc", password="Secret123!", role=User.Role.MANAGER
        )
        self.tech = Technology.objects.create(
            name="PostgreSQL",
            tech_type=Technology.TechType.DATABASE,
            version="16",
        )

    def test_create_update_soft_delete_restore_audited(self):
        app = application_create(
            data={
                "name": "CRM",
                "description": "Clientèle",
                "status": Application.Status.PRODUCTION,
                "criticality": Application.Criticality.HIGH,
            },
            technology_ids=[self.tech.pk],
            user=self.user,
        )
        self.assertEqual(app.technologies.count(), 1)
        self.assertTrue(
            AuditLog.objects.filter(
                action="create", entity="Application", entity_id=str(app.pk)
            ).exists()
        )

        application_update(
            application=app,
            data={"description": "CRM Topnet"},
            user=self.user,
        )
        app.refresh_from_db()
        self.assertEqual(app.description, "CRM Topnet")
        self.assertTrue(
            AuditLog.objects.filter(
                action="update", entity="Application", entity_id=str(app.pk)
            ).exists()
        )

        application_soft_delete(application=app, user=self.user)
        app.refresh_from_db()
        self.assertTrue(app.is_deleted)
        self.assertEqual(app.status, Application.Status.RETIRED)

        application_restore(application=app, user=self.user)
        app.refresh_from_db()
        self.assertFalse(app.is_deleted)
        self.assertTrue(
            AuditLog.objects.filter(
                action="restore", entity="Application", entity_id=str(app.pk)
            ).exists()
        )
