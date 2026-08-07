# Squashed duplicate AddField ops — domain/environment already exist in 0001_initial.

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("certificates", "0001_initial"),
        ("domains", "0001_initial"),
        ("environments", "0002_environment_server"),
    ]

    operations = []
