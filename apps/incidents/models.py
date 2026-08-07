from django.conf import settings
from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Incident(TimeStampedModel, SoftDeleteModel):
    """Historique des incidents majeurs liés aux applications."""

    class Impact(models.TextChoices):
        CRITICAL = "critique", "Critique"
        MAJOR = "majeur", "Majeur"
        MINOR = "mineur", "Mineur"
        LOW = "faible", "Faible"

    class Status(models.TextChoices):
        OPEN = "ouvert", "Ouvert"
        IN_PROGRESS = "en_cours", "En cours"
        RESOLVED = "resolu", "Résolu"
        CLOSED = "clos", "Clos"

    title = models.CharField("Titre", max_length=255, db_index=True)
    description = models.TextField("Description")
    occurred_at = models.DateTimeField("Date de l'incident", db_index=True)
    impact = models.CharField(
        "Impact",
        max_length=32,
        choices=Impact.choices,
        default=Impact.MAJOR,
        db_index=True,
    )
    root_cause = models.TextField("Cause racine", blank=True)
    solution = models.TextField("Solution", blank=True)
    status = models.CharField(
        "Statut",
        max_length=32,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.PROTECT,
        related_name="incidents",
        verbose_name="Application",
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_incidents",
        verbose_name="Signalé par",
    )

    class Meta:
        ordering = ["-occurred_at", "title"]
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"
