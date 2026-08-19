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


class ServerMetric(models.Model):
    """Point-in-time performance snapshot sent by a VM agent."""

    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name="metrics",
        verbose_name="Serveur",
    )
    hostname = models.CharField("Hostname agent", max_length=255)
    cpu_percent = models.FloatField("CPU %")
    memory_total = models.BigIntegerField("RAM totale (octets)")
    memory_used = models.BigIntegerField("RAM utilisée (octets)")
    memory_percent = models.FloatField("RAM %")
    disk_total = models.BigIntegerField("Disque total (octets)")
    disk_used = models.BigIntegerField("Disque utilisé (octets)")
    disk_percent = models.FloatField("Disque %")
    net_bytes_sent = models.BigIntegerField("Réseau envoyé (octets)", default=0)
    net_bytes_recv = models.BigIntegerField("Réseau reçu (octets)", default=0)
    load_avg_1 = models.FloatField("Load average 1 min", default=0)
    uptime_seconds = models.FloatField("Uptime (secondes)", default=0)
    collected_at = models.DateTimeField("Collecté le", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-collected_at"]
        verbose_name = "Métrique serveur"
        verbose_name_plural = "Métriques serveurs"
        indexes = [
            models.Index(fields=["server", "-collected_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.hostname} — CPU {self.cpu_percent}% @ {self.collected_at}"
