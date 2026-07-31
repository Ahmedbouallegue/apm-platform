from django.db import models

from apps.core.models import TimeStampedModel


class Technology(TimeStampedModel):
    """Technologie du SI (langage, framework, BDD, middleware…)."""

    class TechType(models.TextChoices):
        LANGUAGE = "language", "Langage"
        FRAMEWORK = "framework", "Framework"
        DATABASE = "database", "Base de données"
        MIDDLEWARE = "middleware", "Middleware"
        OS = "os", "Système d'exploitation"
        CLOUD = "cloud", "Cloud / SaaS"
        TOOL = "tool", "Outil"
        OTHER = "other", "Autre"

    name = models.CharField("Nom", max_length=128, db_index=True)
    tech_type = models.CharField(
        "Type",
        max_length=32,
        choices=TechType.choices,
        default=TechType.OTHER,
        db_index=True,
    )
    version = models.CharField("Version", max_length=64, blank=True)
    description = models.TextField("Description", blank=True)

    class Meta:
        ordering = ["name", "version"]
        verbose_name = "Technologie"
        verbose_name_plural = "Technologies"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "version"],
                name="uniq_technology_name_version",
            )
        ]

    def __str__(self) -> str:
        if self.version:
            return f"{self.name} {self.version}"
        return self.name
