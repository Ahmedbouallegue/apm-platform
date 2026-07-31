from django.db.models import Count, Q, QuerySet

from apps.servers.models import Server


def server_list(
    *,
    search: str | None = None,
    server_type: str | None = None,
    datacenter: str | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> QuerySet[Server]:
    qs = Server.objects.annotate(env_count=Count("environments"))
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(ip_address__icontains=search)
            | Q(os__icontains=search)
            | Q(datacenter__icontains=search)
            | Q(notes__icontains=search)
        )
    if server_type:
        qs = qs.filter(server_type=server_type)
    if datacenter:
        qs = qs.filter(datacenter__icontains=datacenter)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("name")


def server_get(*, server_id: int, include_deleted: bool = False) -> Server:
    qs = Server.objects.annotate(env_count=Count("environments"))
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    return qs.get(pk=server_id)
