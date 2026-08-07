from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.incidents.models import Incident

User = get_user_model()


class IncidentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="incmgr", password="Secret123!", role=User.Role.MANAGER
        )
        self.app = Application.objects.create(name="CRM")

    def test_create_incident(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/incidents/",
            {
                "title": "Indisponibilité CRM",
                "description": "Timeout base de données",
                "occurred_at": timezone.now().isoformat(),
                "impact": "majeur",
                "status": "ouvert",
                "application": self.app.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Incident.objects.filter(title="Indisponibilité CRM").exists())


class IncidentWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webinc", password="Secret123!", role=User.Role.MANAGER
        )
        app = Application.objects.create(name="Billing")
        Incident.objects.create(
            title="Erreur batch",
            description="Job nocturne en échec",
            occurred_at=timezone.now(),
            application=app,
        )

    def test_list_page(self):
        self.client.login(username="webinc", password="Secret123!")
        response = self.client.get("/incidents/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Erreur batch")
