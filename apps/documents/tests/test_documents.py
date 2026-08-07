
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.documents.models import Document, Tag

User = get_user_model()


class DocumentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="docmgr", password="Secret123!", role=User.Role.MANAGER
        )
        self.app = Application.objects.create(name="Portail RH")

    def test_create_document_and_tag(self):
        self.client.force_authenticate(self.manager)
        tag_resp = self.client.post("/api/documents/tags/", {"name": "architecture"}, format="json")
        self.assertEqual(tag_resp.status_code, status.HTTP_201_CREATED, tag_resp.data)
        tag_id = tag_resp.data["id"]
        response = self.client.post(
            "/api/documents/",
            {
                "title": "Architecture Portail RH.pdf",
                "file_type": "pdf",
                "category": "architecture",
                "description": "Schéma applicatif",
                "application": self.app.pk,
                "tags": [tag_id],
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Document.objects.filter(title="Architecture Portail RH.pdf").exists())
        self.assertTrue(Tag.objects.filter(name="architecture").exists())


class DocumentWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webdoc", password="Secret123!", role=User.Role.MANAGER
        )
        Document.objects.create(title="Manuel exploitation.docx", category=Document.Category.OPS_MANUAL)

    def test_list_page(self):
        self.client.login(username="webdoc", password="Secret123!")
        response = self.client.get("/documents/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manuel exploitation.docx")
