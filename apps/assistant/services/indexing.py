"""Découpe de texte et construction du corpus APM."""
from __future__ import annotations

from django.db import transaction

from apps.applications.models import Application
from apps.assistant.models import KnowledgeChunk, KnowledgeSource
from apps.assistant.services.embeddings import embed_text
from apps.environments.models import Environment
from apps.servers.models import Server
from apps.technologies.models import Technology


def chunk_text(text: str, *, size: int = 700, overlap: int = 120) -> list[str]:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        chunks.append(cleaned[start:end])
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def _upsert_source(
    *,
    source_type: str,
    source_id: str,
    title: str,
    content: str,
    metadata: dict | None = None,
) -> KnowledgeSource:
    source, _ = KnowledgeSource.objects.update_or_create(
        source_type=source_type,
        source_id=str(source_id),
        defaults={
            "title": title[:255],
            "content": content,
            "metadata": metadata or {},
            "is_active": True,
        },
    )
    return source


@transaction.atomic
def reindex_source(source: KnowledgeSource) -> int:
    source.chunks.all().delete()
    parts = chunk_text(f"{source.title}\n{source.content}")
    created = 0
    for idx, part in enumerate(parts):
        KnowledgeChunk.objects.create(
            source=source,
            chunk_index=idx,
            content=part,
            embedding=embed_text(part),
            token_count=len(part.split()),
        )
        created += 1
    return created


def build_application_document(app: Application) -> str:
    techs = ", ".join(str(t) for t in app.technologies.all()) or "aucune"
    owner = app.owner.get_full_name() if app.owner else "non assigné"
    return (
        f"Application: {app.name}\n"
        f"Description: {app.description or 'N/A'}\n"
        f"Statut: {app.get_status_display()}\n"
        f"Criticité: {app.get_criticality_display()}\n"
        f"Direction métier: {app.business_unit or 'N/A'}\n"
        f"Responsable: {owner}\n"
        f"Utilisateurs: {app.user_count}\n"
        f"MEP: {app.go_live_date or 'N/A'} | Fin de vie: {app.end_of_life_date or 'N/A'}\n"
        f"Technologies: {techs}"
    )


def build_technology_document(tech: Technology) -> str:
    return (
        f"Technologie: {tech.name}\n"
        f"Type: {tech.get_tech_type_display()}\n"
        f"Version: {tech.version or 'N/A'}\n"
        f"Description: {tech.description or 'N/A'}"
    )


def build_environment_document(env: Environment) -> str:
    server = env.server.name if env.server else "non assigné"
    return (
        f"Environnement: {env.name} ({env.get_env_type_display()})\n"
        f"Application: {env.application.name}\n"
        f"URL: {env.url or 'N/A'}\n"
        f"IP: {env.ip_address or 'N/A'}\n"
        f"OS: {env.os or 'N/A'} | CPU: {env.cpu or 'N/A'} | RAM: {env.ram or 'N/A'}\n"
        f"Hébergeur: {env.hosting_provider or 'N/A'}\n"
        f"Serveur: {server}\n"
        f"Docker: {'oui' if env.docker else 'non'} | Kubernetes: {'oui' if env.kubernetes else 'non'}\n"
        f"Actif: {'oui' if env.is_active else 'non'}"
    )


def build_server_document(server: Server) -> str:
    return (
        f"Serveur: {server.name}\n"
        f"IP: {server.ip_address}\n"
        f"Type: {server.get_server_type_display()}\n"
        f"OS: {server.os or 'N/A'} | CPU: {server.cpu or 'N/A'} | RAM: {server.ram or 'N/A'}\n"
        f"Datacenter: {server.datacenter or 'N/A'}\n"
        f"Notes: {server.notes or 'N/A'}\n"
        f"Actif: {'oui' if server.is_active else 'non'}"
    )


def index_applications() -> int:
    count = 0
    for app in Application.objects.filter(is_deleted=False).prefetch_related("technologies", "owner"):
        source = _upsert_source(
            source_type=KnowledgeSource.SourceType.APPLICATION,
            source_id=str(app.pk),
            title=app.name,
            content=build_application_document(app),
            metadata={"status": app.status, "criticality": app.criticality},
        )
        count += reindex_source(source)
    return count


def index_technologies() -> int:
    count = 0
    for tech in Technology.objects.all():
        source = _upsert_source(
            source_type=KnowledgeSource.SourceType.TECHNOLOGY,
            source_id=str(tech.pk),
            title=str(tech),
            content=build_technology_document(tech),
            metadata={"tech_type": tech.tech_type},
        )
        count += reindex_source(source)
    return count


def index_environments() -> int:
    count = 0
    for env in Environment.objects.select_related("application", "server"):
        source = _upsert_source(
            source_type=KnowledgeSource.SourceType.ENVIRONMENT,
            source_id=str(env.pk),
            title=str(env),
            content=build_environment_document(env),
            metadata={"env_type": env.env_type, "application_id": env.application_id},
        )
        count += reindex_source(source)
    return count


def index_servers() -> int:
    count = 0
    for server in Server.objects.filter(is_deleted=False):
        source = _upsert_source(
            source_type=KnowledgeSource.SourceType.SERVER,
            source_id=str(server.pk),
            title=server.name,
            content=build_server_document(server),
            metadata={"server_type": server.server_type, "datacenter": server.datacenter},
        )
        count += reindex_source(source)
    return count


def index_manual_notes() -> int:
    count = 0
    for source in KnowledgeSource.objects.filter(
        source_type=KnowledgeSource.SourceType.MANUAL, is_active=True
    ):
        count += reindex_source(source)
    return count


def reindex_all() -> dict:
    return {
        "applications": index_applications(),
        "technologies": index_technologies(),
        "environments": index_environments(),
        "servers": index_servers(),
        "manual": index_manual_notes(),
        "sources": KnowledgeSource.objects.filter(is_active=True).count(),
        "chunks": KnowledgeChunk.objects.count(),
    }
