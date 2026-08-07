from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Journal d'audit append-only des actions plateforme."""

    action = models.CharField("Action", max_length=64, db_index=True)
    entity = models.CharField("Entité", max_length=64, db_index=True)
    entity_id = models.CharField("ID entité", max_length=64, blank=True, db_index=True)
    details = models.TextField("Détails", blank=True)
    occurred_at = models.DateTimeField("Date de l'action", auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Utilisateur",
    )
    ip_address = models.GenericIPAddressField("Adresse IP", null=True, blank=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name = "Entrée d'audit"
        verbose_name_plural = "Journal d'audit"

    def __str__(self) -> str:
        return f"{self.action} {self.entity}#{self.entity_id}"
