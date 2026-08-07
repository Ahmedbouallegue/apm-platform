# Generated manually for Sprint 2

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("applications", "0001_initial"),
        ("domains", "0001_initial"),
        ("environments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Certificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("common_name", models.CharField(db_index=True, max_length=255, verbose_name="Nom commun (CN)")),
                ("san_domains", models.TextField(blank=True, verbose_name="SAN / domaines alternatifs")),
                ("issuer", models.CharField(blank=True, max_length=255, verbose_name="Autorité (CA)")),
                (
                    "certificate_type",
                    models.CharField(
                        choices=[
                            ("single", "Simple"),
                            ("wildcard", "Wildcard"),
                            ("multi_domain", "Multi-domaines"),
                            ("internal", "Interne"),
                        ],
                        db_index=True,
                        default="single",
                        max_length=32,
                        verbose_name="Type",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("valid", "Valide"),
                            ("expiring", "Bientôt expiré"),
                            ("expired", "Expiré"),
                            ("revoked", "Révoqué"),
                        ],
                        db_index=True,
                        default="valid",
                        max_length=32,
                        verbose_name="Statut",
                    ),
                ),
                ("issued_at", models.DateField(blank=True, null=True, verbose_name="Date d'émission")),
                ("expires_at", models.DateField(db_index=True, verbose_name="Date d'expiration")),
                ("auto_renew", models.BooleanField(default=False, verbose_name="Renouvellement auto")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Actif")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="certificates",
                        to="applications.application",
                        verbose_name="Application",
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="certificates",
                        to="domains.domain",
                        verbose_name="Domaine",
                    ),
                ),
                (
                    "environment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="certificates",
                        to="environments.environment",
                        verbose_name="Environnement",
                    ),
                ),
            ],
            options={
                "verbose_name": "Certificat SSL",
                "verbose_name_plural": "Certificats SSL",
                "ordering": ["expires_at", "common_name"],
            },
        ),
    ]
