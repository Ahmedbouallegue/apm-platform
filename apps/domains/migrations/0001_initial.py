# Generated manually for Sprint 2

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("applications", "0001_initial"),
        ("environments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Domain",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "fqdn",
                    models.CharField(
                        db_index=True,
                        max_length=255,
                        unique=True,
                        verbose_name="Nom de domaine (FQDN)",
                    ),
                ),
                ("registrar", models.CharField(blank=True, max_length=255, verbose_name="Registrar")),
                ("dns_provider", models.CharField(blank=True, max_length=255, verbose_name="Fournisseur DNS")),
                ("registered_at", models.DateField(blank=True, null=True, verbose_name="Date d'enregistrement")),
                (
                    "expires_at",
                    models.DateField(blank=True, db_index=True, null=True, verbose_name="Date d'expiration"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Actif"),
                            ("expiring", "Bientôt expiré"),
                            ("expired", "Expiré"),
                            ("transferred", "Transféré"),
                            ("parked", "Parké"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=32,
                        verbose_name="Statut",
                    ),
                ),
                ("is_primary", models.BooleanField(default=False, verbose_name="Domaine principal")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Actif")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="domains",
                        to="applications.application",
                        verbose_name="Application",
                    ),
                ),
                (
                    "environment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="domains",
                        to="environments.environment",
                        verbose_name="Environnement",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nom de domaine",
                "verbose_name_plural": "Noms de domaine",
                "ordering": ["fqdn"],
            },
        ),
    ]
