from django.db.models import Q, QuerySet

from apps.environments.models import Environment


def environment_list(
    *,
    search: str | None = None,
    env_type: str | None = None,
    application_id: int | None = None,
    is_active: bool | None = None,
) -> QuerySet[Environment]:
    qs = Environment.objects.select_related("application", "server")
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(url__icontains=search)
            | Q(ip_address__icontains=search)
            | Q(application__name__icontains=search)
            | Q(hosting_provider__icontains=search)
            | Q(os__icontains=search)
            | Q(server__name__icontains=search)
        )
    if env_type:
        qs = qs.filter(env_type=env_type)
    if application_id:
        qs = qs.filter(application_id=application_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("application__name", "env_type")


def environment_get(*, environment_id: int) -> Environment:
    return Environment.objects.select_related("application", "server").get(pk=environment_id)
