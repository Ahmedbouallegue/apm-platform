from django.conf import settings
from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Tag(TimeStampedModel):
    """Mot-clé pour la recherche documentaire."""

    name = models.CharField("Nom", max_length=64, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self) -> str:
        return self.name


class Document(TimeStampedModel, SoftDeleteModel):
    """Documentation liée aux applications."""

    class Category(models.TextChoices):
        ARCHITECTURE = "architecture", "Architecture"
        USER_MANUAL = "manuel_utilisateur", "Manuel utilisateur"
        OPS_MANUAL = "manuel_exploitation", "Manuel exploitation"
        CONTRACT = "contrat", "Contrat"
        PROCEDURE = "procedure", "Procédure"

    title = models.CharField("Nom du fichier", max_length=255, db_index=True)
    file_type = models.CharField("Type de fichier", max_length=64, blank=True)
    category = models.CharField(
        "Catégorie",
        max_length=32,
        choices=Category.choices,
        default=Category.ARCHITECTURE,
        db_index=True,
    )
    description = models.TextField("Description", blank=True)
    file = models.FileField("Fichier", upload_to="documents/%Y/%m/", blank=True)
    uploaded_at = models.DateTimeField("Date d'upload", auto_now_add=True, db_index=True)
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Application",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
        verbose_name="Déposé par",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="documents", verbose_name="Tags")
    is_active = models.BooleanField("Actif", default=True, db_index=True)

    class Meta:
        ordering = ["-uploaded_at", "title"]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self) -> str:
        return self.title
