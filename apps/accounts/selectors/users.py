from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

User = get_user_model()


def user_list(*, search: str | None = None, role: str | None = None, is_active: bool | None = None) -> QuerySet:
    qs = User.objects.all().order_by("username")
    if search:
        qs = qs.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(department__icontains=search)
        )
    if role:
        qs = qs.filter(role=role)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def user_get(*, user_id: int) -> User:
    return User.objects.get(pk=user_id)
