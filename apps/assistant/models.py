from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class KnowledgeSource(TimeStampedModel):
    """Source de connaissance indexée pour le RAG."""

    class SourceType(models.TextChoices):
        APPLICATION = "application", "Application"
        TECHNOLOGY = "technology", "Technologie"
        ENVIRONMENT = "environment", "Environnement"
        SERVER = "server", "Serveur"
        MANUAL = "manual", "Note manuelle"
        DOCUMENT = "document", "Document"

    source_type = models.CharField(max_length=32, choices=SourceType.choices, db_index=True)
    source_id = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Source de connaissance"
        verbose_name_plural = "Sources de connaissance"
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_id"],
                name="uniq_knowledge_source_ref",
            )
        ]

    def __str__(self) -> str:
        return f"[{self.get_source_type_display()}] {self.title}"


class KnowledgeChunk(TimeStampedModel):
    """Fragment indexé avec embedding pour la recherche sémantique."""

    source = models.ForeignKey(
        KnowledgeSource,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField(default=0)
    content = models.TextField()
    embedding = models.JSONField(default=list, blank=True)
    token_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["source_id", "chunk_index"]
        verbose_name = "Chunk RAG"
        verbose_name_plural = "Chunks RAG"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "chunk_index"],
                name="uniq_chunk_per_source",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source_id}#{self.chunk_index}"


class ChatSession(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Session chat"
        verbose_name_plural = "Sessions chat"

    def __str__(self) -> str:
        return self.title or f"Session #{self.pk}"


class ChatMessage(TimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "Utilisateur"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "Système"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message chat"
        verbose_name_plural = "Messages chat"
