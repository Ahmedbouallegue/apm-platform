from django.db import models

from apps.core.models import TimeStampedModel


class Environment(TimeStampedModel):
    """Environnement d'exécution d'une application (DEV → PROD)."""

    class EnvType(models.TextChoices):
        DEV = "dev", "DEV"
        RECETTE = "recette", "RECETTE"
        PREPROD = "preprod", "PREPROD"
        PROD = "prod", "PROD"

    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="environments",
        verbose_name="Application",
    )
    server = models.ForeignKey(
        "servers.Server",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="environments",
        verbose_name="Serveur",
    )
    name = models.CharField("Nom", max_length=255)
    env_type = models.CharField(
        "Type d'environnement",
        max_length=16,
        choices=EnvType.choices,
        db_index=True,
    )
    url = models.URLField("URL", blank=True)
    ip_address = models.GenericIPAddressField("Adresse IP", null=True, blank=True)
    os = models.CharField("Système d'exploitation", max_length=128, blank=True)
    cpu = models.CharField("CPU", max_length=64, blank=True)
    ram = models.CharField("RAM", max_length=64, blank=True)
    hosting_provider = models.CharField("Hébergeur", max_length=255, blank=True)
    docker = models.BooleanField("Docker", default=False)
    kubernetes = models.BooleanField("Kubernetes", default=False)
    is_active = models.BooleanField("Actif", default=True, db_index=True)

    class Meta:
        ordering = ["application__name", "env_type"]
        verbose_name = "Environnement"
        verbose_name_plural = "Environnements"
        constraints = [
            models.UniqueConstraint(
                fields=["application", "env_type"],
                name="uniq_application_env_type",
            )
        ]

    def __str__(self) -> str:
        return f"{self.application.name} — {self.get_env_type_display()}"
