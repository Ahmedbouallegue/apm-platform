from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Dependency(TimeStampedModel, SoftDeleteModel):
    """Dépendance applicative pour la cartographie du SI."""

    class DependencyType(models.TextChoices):
        API = "api", "API"
        DATABASE = "base_donnees", "Base de données"
        FILE = "fichier", "Fichier / batch"
        MESSAGE = "message", "Messagerie"
        AUTH = "auth", "Authentification"
        OTHER = "autre", "Autre"

    dependency_type = models.CharField(
        "Type de dépendance",
        max_length=32,
        choices=DependencyType.choices,
        default=DependencyType.API,
        db_index=True,
    )
    description = models.TextField("Description", blank=True)
    source_application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="dependencies_out",
        verbose_name="Application source",
    )
    target_application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="dependencies_in",
        verbose_name="Application cible",
    )
    target_external = models.CharField(
        "Cible externe",
        max_length=255,
        blank=True,
        help_text="Ex. Active Directory, PostgreSQL, API tierce…",
    )
    is_active = models.BooleanField("Actif", default=True, db_index=True)

    class Meta:
        ordering = ["source_application__name", "dependency_type"]
        verbose_name = "Dépendance applicative"
        verbose_name_plural = "Dépendances applicatives"

    def __str__(self) -> str:
        target = self.target_application.name if self.target_application else self.target_external
        return f"{self.source_application} → {target}"

    def clean(self):
        if not self.target_application and not self.target_external:
            raise ValidationError("Indiquez une application cible ou une cible externe.")
        if self.target_application and self.target_external:
            raise ValidationError("Choisissez soit une application cible, soit une cible externe.")
        if self.target_application_id and self.source_application_id == self.target_application_id:
            raise ValidationError("Une application ne peut pas dépendre d'elle-même.")
