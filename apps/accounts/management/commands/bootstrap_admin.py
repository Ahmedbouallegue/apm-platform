"""
Crée un compte administrateur initial Topnet APM.

Usage:
  python manage.py bootstrap_admin --username admin --password 'ChangeMe123!' --email admin@topnet.tn
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.accounts.services.users import user_create


class Command(BaseCommand):
    help = "Bootstrap an initial Topnet APM administrator"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default="Admin123!")
        parser.add_argument("--email", default="admin@topnet.tn")

    def handle(self, *args, **options):
        username = options["username"]
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User « {username} » already exists."))
            return

        user_create(
            username=username,
            email=options["email"],
            password=options["password"],
            first_name="Admin",
            last_name="Topnet",
            role=User.Role.ADMIN,
            department="DSI",
            is_staff=True,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Administrator « {username} » created."))
