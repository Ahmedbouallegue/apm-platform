from django.contrib.auth import get_user_model
from django.db import transaction

from apps.audit.services.audit import audit_log_create

User = get_user_model()

STAFF_ROLES = frozenset({User.Role.ADMIN, User.Role.DSI})


def _apply_staff_flag(user: User) -> None:
    if user.role in STAFF_ROLES:
        user.is_staff = True


@transaction.atomic
def user_create(
    *,
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    role: str = User.Role.DSI,
    phone: str = "",
    department: str = "",
    is_staff: bool = False,
    is_active: bool = True,
    actor=None,
) -> User:
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone=phone,
        department=department,
        is_staff=is_staff or role in STAFF_ROLES,
        is_active=is_active,
    )
    user.set_password(password)
    user.full_clean()
    user.save()
    audit_log_create(
        action="create",
        entity="User",
        entity_id=user.pk,
        details=f"Utilisateur « {user.username} » créé (rôle {user.role})",
        user=actor,
    )
    return user


@transaction.atomic
def user_update(*, user: User, data: dict, actor=None) -> User:
    password = data.pop("password", None)
    for field, value in data.items():
        setattr(user, field, value)
    if "role" in data:
        _apply_staff_flag(user)
    if password:
        user.set_password(password)
    user.full_clean()
    user.save()
    audit_log_create(
        action="update",
        entity="User",
        entity_id=user.pk,
        details=f"Utilisateur « {user.username} » mis à jour",
        user=actor,
    )
    return user


@transaction.atomic
def user_deactivate(*, user: User, actor=None) -> User:
    user.is_active = False
    user.save(update_fields=["is_active", "updated_at"])
    audit_log_create(
        action="deactivate",
        entity="User",
        entity_id=user.pk,
        details=f"Compte « {user.username} » désactivé",
        user=actor,
    )
    return user


@transaction.atomic
def user_activate(*, user: User, actor=None) -> User:
    user.is_active = True
    user.save(update_fields=["is_active", "updated_at"])
    audit_log_create(
        action="activate",
        entity="User",
        entity_id=user.pk,
        details=f"Compte « {user.username} » réactivé",
        user=actor,
    )
    return user


@transaction.atomic
def user_delete(*, user: User, actor=None) -> None:
    username = user.username
    user_pk = user.pk
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        OutstandingToken.objects.filter(user=user).delete()
    except Exception:
        pass
    user.delete()
    audit_log_create(
        action="delete",
        entity="User",
        entity_id=user_pk,
        details=f"Utilisateur « {username} » supprimé définitivement",
        user=actor,
    )
