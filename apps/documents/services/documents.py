from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.documents.models import Document, Tag


@transaction.atomic
def tag_create(*, name: str) -> Tag:
    tag = Tag(name=name.strip())
    tag.full_clean()
    tag.save()
    return tag


@transaction.atomic
def tag_get_or_create(*, name: str) -> Tag:
    tag, _ = Tag.objects.get_or_create(name=name.strip())
    return tag


@transaction.atomic
def document_create(*, data: dict, tag_names: list[str] | None = None, user=None) -> Document:
    tags = data.pop("tags", None)
    document = Document(**data)
    if user and not document.uploaded_by_id:
        document.uploaded_by = user
    document.full_clean()
    document.save()
    if tags is not None:
        document.tags.set(tags)
    elif tag_names:
        tag_objs = [tag_get_or_create(name=n) for n in tag_names if n.strip()]
        document.tags.set(tag_objs)
    audit_log_create(
        action="create",
        entity="Document",
        entity_id=document.pk,
        details=f"Document « {document.title} » créé",
        user=user,
    )
    return document


@transaction.atomic
def document_update(*, document: Document, data: dict, user=None) -> Document:
    tags = data.pop("tags", None)
    for field, value in data.items():
        setattr(document, field, value)
    document.full_clean()
    document.save()
    if tags is not None:
        document.tags.set(tags)
    audit_log_create(
        action="update",
        entity="Document",
        entity_id=document.pk,
        details=f"Document « {document.title} » mis à jour",
        user=user,
    )
    return document


@transaction.atomic
def document_soft_delete(*, document: Document, user=None) -> Document:
    document.is_deleted = True
    document.deleted_at = timezone.now()
    document.is_active = False
    document.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    audit_log_create(
        action="delete",
        entity="Document",
        entity_id=document.pk,
        details=f"Document « {document.title} » archivé",
        user=user,
    )
    return document
