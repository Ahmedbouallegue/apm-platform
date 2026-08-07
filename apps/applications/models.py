from django.conf import settings
from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Application(TimeStampedModel, SoftDeleteModel):
    """Catalogue applicatif — patrimoine SI."""

    class Criticality(models.TextChoices):
        CRITICAL = "critical", "Critique"
        HIGH = "high", "Haute"
        MEDIUM = "medium", "Moyenne"
        LOW = "low", "Basse"

    class Status(models.TextChoices):
        PROJECT = "project", "En projet"
        PRODUCTION = "production", "En production"
        MAINTENANCE = "maintenance", "En maintenance"
        DEPRECATED = "deprecated", "Obsolète"
        RETIRED = "retired", "Retirée"

    name = models.CharField("Nom", max_length=255, unique=True, db_index=True)
    description = models.TextField("Description", blank=True)
    criticality = models.CharField(
        "Criticité",
        max_length=32,
        choices=Criticality.choices,
        default=Criticality.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        "Statut",
        max_length=32,
        choices=Status.choices,
        default=Status.PROJECT,
        db_index=True,
    )
    go_live_date = models.DateField("Date de mise en production", null=True, blank=True)
    end_of_life_date = models.DateField("Date de fin de vie", null=True, blank=True)
    user_count = models.PositiveIntegerField("Nombre d'utilisateurs", default=0)
    business_unit = models.CharField("Direction métier", max_length=255, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_applications",
        verbose_name="Responsable",
    )
    technologies = models.ManyToManyField(
        "technologies.Technology",
        blank=True,
        related_name="applications",
        verbose_name="Technologies",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        indexes = [
            models.Index(
                fields=["is_deleted", "status"],
                name="app_deleted_status_idx",
            ),
            models.Index(
                fields=["is_deleted", "criticality"],
                name="app_deleted_crit_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name
