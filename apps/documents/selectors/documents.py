from django.db.models import Prefetch, Q, QuerySet

from apps.documents.models import Document, Tag


def tag_list(*, search: str | None = None) -> QuerySet[Tag]:
    qs = Tag.objects.all()
    if search:
        qs = qs.filter(name__icontains=search)
    return qs.order_by("name")


def document_list(
    *,
    search: str | None = None,
    category: str | None = None,
    application_id: int | None = None,
    tag: str | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> QuerySet[Document]:
    qs = Document.objects.select_related("application", "uploaded_by").prefetch_related("tags")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(file_type__icontains=search)
            | Q(tags__name__icontains=search)
        ).distinct()
    if category:
        qs = qs.filter(category=category)
    if application_id:
        qs = qs.filter(application_id=application_id)
    if tag:
        qs = qs.filter(tags__name__iexact=tag)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("-uploaded_at", "title")
