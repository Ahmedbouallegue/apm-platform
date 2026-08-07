from django.db.models import Q, QuerySet

from apps.dependencies.models import Dependency


def dependency_list(
    *,
    search: str | None = None,
    dependency_type: str | None = None,
    source_id: int | None = None,
    target_id: int | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> QuerySet[Dependency]:
    qs = Dependency.objects.select_related("source_application", "target_application")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(description__icontains=search)
            | Q(target_external__icontains=search)
            | Q(source_application__name__icontains=search)
            | Q(target_application__name__icontains=search)
        )
    if dependency_type:
        qs = qs.filter(dependency_type=dependency_type)
    if source_id:
        qs = qs.filter(source_application_id=source_id)
    if target_id:
        qs = qs.filter(target_application_id=target_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("source_application__name", "dependency_type")
