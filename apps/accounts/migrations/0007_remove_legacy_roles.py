# Generated manually — retire manager / viewer roles

from django.db import migrations, models


def migrate_legacy_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="manager").update(role="dsi")
    User.objects.filter(role="viewer").update(role="dsi")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_alter_user_role_add_system"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Administrateur"),
                    ("dsi", "Administrateur DSI"),
                    ("system", "Administrateur Système"),
                ],
                db_index=True,
                default="dsi",
                max_length=32,
            ),
        ),
    ]
