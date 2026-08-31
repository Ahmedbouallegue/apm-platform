"""
Supprime tous les comptes utilisateurs et recrée le jeu par défaut (3 rôles).

Usage:
  python manage.py reset_users --yes
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.seed_users import format_user_credentials, seed_default_users
from apps.notifications.models import Notification

User = get_user_model()


def _delete_all_users() -> int:
    """Supprime tous les comptes et données liées (notifications, sessions JWT)."""
    count = User.objects.count()
    if count == 0:
        return 0

    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        BlacklistedToken.objects.all().delete()
        OutstandingToken.objects.all().delete()
    except Exception:
        pass

    Notification.objects.all().delete()
    Session.objects.all().delete()
    User.objects.all().delete()
    return count


class Command(BaseCommand):
    help = "Supprime tous les utilisateurs et recrée les comptes Topnet APM par défaut"

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirme la suppression de tous les comptes existants",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError(
                "Cette commande supprime TOUS les comptes utilisateurs.\n"
                "Relancez avec --yes pour confirmer."
            )

        with transaction.atomic():
            removed = _delete_all_users()
            users = seed_default_users()

        self.stdout.write(self.style.WARNING(f"{removed} compte(s) supprimé(s)."))
        self.stdout.write(self.style.SUCCESS(f"{len(users)} compte(s) créé(s)."))
        self.stdout.write("Nouveaux comptes :")
        for line in format_user_credentials():
            self.stdout.write(line)
        self.stdout.write("")
        self.stdout.write("Rôles : admin (utilisateurs), dsi (patrimoine), system (infra).")
