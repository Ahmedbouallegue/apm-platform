from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Domain(TimeStampedModel, SoftDeleteModel):
    """Nom de domaine du patrimoine applicatif."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Actif"
        EXPIRING = "expiring", "Bientôt expiré"
        EXPIRED = "expired", "Expiré"
        TRANSFERRED = "transferred", "Transféré"
        PARKED = "parked", "Parké"

    fqdn = models.CharField("Nom de domaine (FQDN)", max_length=255, unique=True, db_index=True)
    registrar = models.CharField("Registrar", max_length=255, blank=True)
    dns_provider = models.CharField("Fournisseur DNS", max_length=255, blank=True)
    registered_at = models.DateField("Date d'enregistrement", null=True, blank=True)
    expires_at = models.DateField("Date d'expiration", null=True, blank=True, db_index=True)
    status = models.CharField(
        "Statut",
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="domains",
        verbose_name="Application",
    )
    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="domains",
        verbose_name="Environnement",
    )
    is_primary = models.BooleanField("Domaine principal", default=False)
    auto_renew = models.BooleanField("Renouvellement automatique", default=False)
    is_active = models.BooleanField("Actif", default=True, db_index=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["fqdn"]
        verbose_name = "Nom de domaine"
        verbose_name_plural = "Noms de domaine"

    def __str__(self) -> str:
        return self.fqdn
