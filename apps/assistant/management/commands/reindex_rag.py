from django.core.management.base import BaseCommand

from apps.assistant.services.indexing import reindex_all


class Command(BaseCommand):
    help = "Réindexe le patrimoine APM pour l'assistant RAG"

    def handle(self, *args, **options):
        stats = reindex_all()
        self.stdout.write(self.style.SUCCESS(f"Réindexation terminée: {stats}"))
