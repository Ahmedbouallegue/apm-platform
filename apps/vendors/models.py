from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Vendor(TimeStampedModel, SoftDeleteModel):
    """Fournisseur SI (hébergeur, éditeur, mainteneur, télécom…)."""

    class VendorType(models.TextChoices):
        HOSTING = "hosting", "Hébergement"
        SOFTWARE = "software", "Éditeur logiciel"
        MAINTENANCE = "maintenance", "Maintenance"
        TELECOM = "telecom", "Télécom"
        SECURITY = "security", "Sécurité"
        OTHER = "other", "Autre"

    name = models.CharField("Nom", max_length=255, unique=True, db_index=True)
    vendor_type = models.CharField(
        "Type",
        max_length=32,
        choices=VendorType.choices,
        default=VendorType.OTHER,
        db_index=True,
    )
    contact_name = models.CharField("Contact", max_length=255, blank=True)
    contact_email = models.EmailField("Email contact", blank=True)
    contact_phone = models.CharField("Téléphone", max_length=32, blank=True)
    website = models.URLField("Site web", blank=True)
    address = models.TextField("Adresse", blank=True)
    is_active = models.BooleanField("Actif", default=True, db_index=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"

    def __str__(self) -> str:
        return self.name
