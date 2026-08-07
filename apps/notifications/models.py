from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """Alerte ou notification destinée à un utilisateur."""

    class NotificationType(models.TextChoices):
        INFO = "info", "Information"
        ALERT = "alerte", "Alerte"
        EXPIRY = "expiration", "Expiration"
        INCIDENT = "incident", "Incident"
        SYSTEM = "systeme", "Système"

    class Status(models.TextChoices):
        UNREAD = "non_lue", "Non lue"
        READ = "lue", "Lue"
        ARCHIVED = "archivee", "Archivée"

    title = models.CharField("Titre", max_length=255)
    message = models.TextField("Message")
    notification_type = models.CharField(
        "Type",
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
    )
    sent_at = models.DateTimeField("Date d'envoi", auto_now_add=True, db_index=True)
    status = models.CharField(
        "Statut",
        max_length=32,
        choices=Status.choices,
        default=Status.UNREAD,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinataire",
    )
    link = models.CharField("Lien relatif", max_length=255, blank=True)

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self) -> str:
        return f"{self.title} → {self.user}"


class PlatformSettings(TimeStampedModel):
    """Paramètres globaux APM (singleton pk=1) — Administrateur DSI."""

    alert_days_60 = models.PositiveSmallIntegerField(
        "Seuil alerte J-60 (jours)",
        default=60,
        help_text="Bande d’alerte anticipée (ex. 60 jours avant échéance).",
    )
    alert_days_30 = models.PositiveSmallIntegerField(
        "Seuil alerte J-30 (jours)",
        default=30,
        help_text="Bande d’alerte rapprochée (ex. 30 jours avant échéance).",
    )
    alert_on_expiry = models.BooleanField(
        "Alerte le jour d’expiration (J-0)",
        default=True,
    )
    alert_cooldown_days = models.PositiveSmallIntegerField(
        "Délai anti-doublon (jours)",
        default=7,
        help_text="Ne pas renvoyer la même alerte (ressource + seuil) avant N jours.",
    )

    class Meta:
        verbose_name = "Paramètres plateforme"
        verbose_name_plural = "Paramètres plateforme"

    def __str__(self) -> str:
        return "Paramètres APM"

    @classmethod
    def load(cls) -> "PlatformSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def thresholds(self) -> list[int]:
        values = [int(self.alert_days_60), int(self.alert_days_30)]
        if self.alert_on_expiry:
            values.append(0)
        return sorted({max(0, v) for v in values})
