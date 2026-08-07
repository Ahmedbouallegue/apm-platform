# Generated manually for Sprint 2

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Vendor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(db_index=True, max_length=255, unique=True, verbose_name="Nom")),
                (
                    "vendor_type",
                    models.CharField(
                        choices=[
                            ("hosting", "Hébergement"),
                            ("software", "Éditeur logiciel"),
                            ("maintenance", "Maintenance"),
                            ("telecom", "Télécom"),
                            ("security", "Sécurité"),
                            ("other", "Autre"),
                        ],
                        db_index=True,
                        default="other",
                        max_length=32,
                        verbose_name="Type",
                    ),
                ),
                ("contact_name", models.CharField(blank=True, max_length=255, verbose_name="Contact")),
                ("contact_email", models.EmailField(blank=True, max_length=254, verbose_name="Email contact")),
                ("contact_phone", models.CharField(blank=True, max_length=32, verbose_name="Téléphone")),
                ("website", models.URLField(blank=True, verbose_name="Site web")),
                ("address", models.TextField(blank=True, verbose_name="Adresse")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Actif")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
            ],
            options={
                "verbose_name": "Fournisseur",
                "verbose_name_plural": "Fournisseurs",
                "ordering": ["name"],
            },
        ),
    ]
