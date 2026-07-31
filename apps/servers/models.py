from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Server(TimeStampedModel, SoftDeleteModel):
    """Inventaire des serveurs hébergeant les environnements applicatifs."""

    class ServerType(models.TextChoices):
        PHYSICAL = "physical", "Physique"
        VM = "vm", "VM"
        CLOUD = "cloud", "Cloud"

    name = models.CharField("Nom", max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField("Adresse IP", unique=True)
    os = models.CharField("Système d'exploitation", max_length=128, blank=True)
    cpu = models.CharField("CPU", max_length=64, blank=True)
    ram = models.CharField("RAM", max_length=64, blank=True)
    datacenter = models.CharField("Datacenter", max_length=255, blank=True, db_index=True)
    server_type = models.CharField(
        "Type de serveur",
        max_length=16,
        choices=ServerType.choices,
        default=ServerType.VM,
        db_index=True,
    )
    is_active = models.BooleanField("Actif", default=True, db_index=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Serveur"
        verbose_name_plural = "Serveurs"

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"
