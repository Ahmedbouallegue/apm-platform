# Generated manually for role split (admin / dsi / system)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_alter_user_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Administrateur"),
                    ("dsi", "Administrateur DSI"),
                    ("system", "Administrateur Système"),
                    ("manager", "Équipe DSI / Technicien"),
                    ("viewer", "Lecteur"),
                ],
                db_index=True,
                default="viewer",
                max_length=32,
            ),
        ),
    ]
