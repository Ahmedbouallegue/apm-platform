from django.conf import settings
from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Contract(TimeStampedModel, SoftDeleteModel):
    """Contrat de maintenance, support, licence ou hébergement."""

    class ContractType(models.TextChoices):
        MAINTENANCE = "maintenance", "Maintenance"
        SUPPORT = "support", "Support"
        LICENSE = "license", "Licence"
        HOSTING = "hosting", "Hébergement"
        SLA = "sla", "SLA"

    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        ACTIVE = "active", "Actif"
        EXPIRING = "expiring", "Bientôt expiré"
        EXPIRED = "expired", "Expiré"
        TERMINATED = "terminated", "Résilié"

    reference = models.CharField("Référence", max_length=64, unique=True, db_index=True)
    title = models.CharField("Intitulé", max_length=255)
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="contracts",
        verbose_name="Fournisseur",
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
        verbose_name="Application couverte",
    )
    contract_type = models.CharField(
        "Type de contrat",
        max_length=32,
        choices=ContractType.choices,
        default=ContractType.MAINTENANCE,
        db_index=True,
    )
    status = models.CharField(
        "Statut",
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    start_date = models.DateField("Date de début")
    end_date = models.DateField("Date de fin", db_index=True)
    annual_cost = models.DecimalField(
        "Coût annuel",
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    currency = models.CharField("Devise", max_length=3, default="TND")
    auto_renew = models.BooleanField("Renouvellement auto", default=False)
    sla_level = models.CharField("Niveau SLA", max_length=64, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_contracts",
        verbose_name="Responsable DSI",
    )
    is_active = models.BooleanField("Actif", default=True, db_index=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["-end_date", "reference"]
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        indexes = [
            models.Index(
                fields=["is_deleted", "is_active", "end_date"],
                name="contract_active_end_idx",
            ),
            models.Index(
                fields=["is_deleted", "status"],
                name="contract_deleted_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reference} — {self.title}"
