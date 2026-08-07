from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Certificate(TimeStampedModel, SoftDeleteModel):
    """Certificat SSL/TLS du patrimoine applicatif."""

    class CertificateType(models.TextChoices):
        SINGLE = "single", "Simple"
        WILDCARD = "wildcard", "Wildcard"
        MULTI = "multi_domain", "Multi-domaines"
        INTERNAL = "internal", "Interne"

    class Status(models.TextChoices):
        VALID = "valid", "Valide"
        EXPIRING = "expiring", "Bientôt expiré"
        EXPIRED = "expired", "Expiré"
        REVOKED = "revoked", "Révoqué"

    common_name = models.CharField("Nom commun (CN)", max_length=255, db_index=True)
    san_domains = models.TextField("SAN / domaines alternatifs", blank=True)
    issuer = models.CharField("Autorité (CA)", max_length=255, blank=True)
    certificate_type = models.CharField(
        "Type",
        max_length=32,
        choices=CertificateType.choices,
        default=CertificateType.SINGLE,
        db_index=True,
    )
    status = models.CharField(
        "Statut",
        max_length=32,
        choices=Status.choices,
        default=Status.VALID,
        db_index=True,
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
        verbose_name="Application",
    )
    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
        verbose_name="Environnement",
    )
    domain = models.ForeignKey(
        "domains.Domain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
        verbose_name="Domaine",
    )
    issued_at = models.DateField("Date d'émission", null=True, blank=True)
    expires_at = models.DateField("Date d'expiration", db_index=True)
    auto_renew = models.BooleanField("Renouvellement auto", default=False)
    is_active = models.BooleanField("Actif", default=True, db_index=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        ordering = ["expires_at", "common_name"]
        verbose_name = "Certificat SSL"
        verbose_name_plural = "Certificats SSL"
        indexes = [
            models.Index(
                fields=["is_deleted", "is_active", "expires_at"],
                name="cert_active_expiry_idx",
            ),
            models.Index(
                fields=["is_deleted", "status"],
                name="cert_deleted_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.common_name} ({self.get_status_display()})"
