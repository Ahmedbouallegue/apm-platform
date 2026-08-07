# Generated manually for Sprint 2

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("applications", "0001_initial"),
        ("vendors", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Contract",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("reference", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="Référence")),
                ("title", models.CharField(max_length=255, verbose_name="Intitulé")),
                (
                    "contract_type",
                    models.CharField(
                        choices=[
                            ("maintenance", "Maintenance"),
                            ("support", "Support"),
                            ("license", "Licence"),
                            ("hosting", "Hébergement"),
                            ("sla", "SLA"),
                        ],
                        db_index=True,
                        default="maintenance",
                        max_length=32,
                        verbose_name="Type de contrat",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Brouillon"),
                            ("active", "Actif"),
                            ("expiring", "Bientôt expiré"),
                            ("expired", "Expiré"),
                            ("terminated", "Résilié"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=32,
                        verbose_name="Statut",
                    ),
                ),
                ("start_date", models.DateField(verbose_name="Date de début")),
                ("end_date", models.DateField(db_index=True, verbose_name="Date de fin")),
                (
                    "annual_cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=3,
                        max_digits=12,
                        null=True,
                        verbose_name="Coût annuel",
                    ),
                ),
                ("currency", models.CharField(default="TND", max_length=3, verbose_name="Devise")),
                ("auto_renew", models.BooleanField(default=False, verbose_name="Renouvellement auto")),
                ("sla_level", models.CharField(blank=True, max_length=64, verbose_name="Niveau SLA")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Actif")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contracts",
                        to="applications.application",
                        verbose_name="Application couverte",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_contracts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsable DSI",
                    ),
                ),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contracts",
                        to="vendors.vendor",
                        verbose_name="Fournisseur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contrat",
                "verbose_name_plural": "Contrats",
                "ordering": ["-end_date", "reference"],
            },
        ),
    ]
