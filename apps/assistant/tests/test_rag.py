from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.assistant.models import KnowledgeChunk, KnowledgeSource
from apps.assistant.services.embeddings import cosine_similarity, local_embed
from apps.assistant.services.indexing import reindex_all
from apps.assistant.services.rag import ask_question
from apps.technologies.models import Technology

User = get_user_model()


class EmbeddingTests(TestCase):
    def test_local_embed_is_deterministic_and_normalized(self):
        a = local_embed("PostgreSQL CRM critique")
        b = local_embed("PostgreSQL CRM critique")
        self.assertEqual(a, b)
        self.assertAlmostEqual(sum(x * x for x in a), 1.0, places=5)
        self.assertGreater(cosine_similarity(a, local_embed("base PostgreSQL")), 0)


class RagPipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="raguser",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.tech = Technology.objects.create(
            name="PostgreSQL",
            tech_type="database",
            version="16",
            description="SGBD relationnel",
        )
        self.app = Application.objects.create(
            name="CRM Topnet",
            description="Gestion de la relation client",
            status="production",
            criticality="high",
            owner=self.user,
        )
        self.app.technologies.add(self.tech)

    def test_reindex_creates_chunks(self):
        stats = reindex_all()
        self.assertGreaterEqual(stats["applications"], 1)
        self.assertGreaterEqual(stats["technologies"], 1)
        self.assertTrue(KnowledgeSource.objects.filter(title="CRM Topnet").exists())
        self.assertGreater(KnowledgeChunk.objects.count(), 0)

    def test_ask_returns_answer_with_sources(self):
        reindex_all()
        result = ask_question(user=self.user, question="Quelles applications utilisent PostgreSQL ?")
        self.assertIn("answer", result)
        self.assertTrue(result["answer"])
        self.assertGreaterEqual(len(result["sources"]), 1)
        self.assertTrue(
            any("PostgreSQL" in s["title"] or "CRM" in s["title"] for s in result["sources"])
            or "PostgreSQL" in result["answer"]
            or "CRM" in result["answer"]
        )


class AssistantAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="aimgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        Application.objects.create(name="Billing", description="Facturation Topnet")

    def test_ask_endpoint(self):
        self.client.force_authenticate(self.manager)
        reindex = self.client.post("/api/assistant/reindex/", {}, format="json")
        self.assertEqual(reindex.status_code, status.HTTP_200_OK, reindex.data)
        response = self.client.post(
            "/api/assistant/ask/",
            {"question": "Parle-moi de Billing"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("answer", response.data)
        self.assertIn("session_id", response.data)

    def test_web_chat_requires_login(self):
        response = self.client.get("/assistant/")
        self.assertEqual(response.status_code, 302)
