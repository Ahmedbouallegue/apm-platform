from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """Custom user model for APM Platform."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrateur DSI"
        DSI = "dsi", "Administrateur DSI (DSI)"
        MANAGER = "manager", "Équipe DSI / Technicien"
        VIEWER = "viewer", "Lecteur"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.VIEWER,
        db_index=True,
    )
    phone = models.CharField(max_length=32, blank=True)
    department = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["username"]
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self) -> str:
        return self.get_username()
