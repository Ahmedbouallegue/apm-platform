from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


@transaction.atomic
def user_create(
    *,
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    role: str = User.Role.VIEWER,
    phone: str = "",
    department: str = "",
    is_staff: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone=phone,
        department=department,
        is_staff=is_staff or role == User.Role.ADMIN,
        is_active=is_active,
    )
    user.set_password(password)
    user.full_clean()
    user.save()
    return user


@transaction.atomic
def user_update(*, user: User, data: dict) -> User:
    password = data.pop("password", None)
    for field, value in data.items():
        setattr(user, field, value)
    if "role" in data and data["role"] == User.Role.ADMIN:
        user.is_staff = True
    if password:
        user.set_password(password)
    user.full_clean()
    user.save()
    return user


@transaction.atomic
def user_deactivate(*, user: User) -> User:
    user.is_active = False
    user.save(update_fields=["is_active", "updated_at"])
    return user


@transaction.atomic
def user_activate(*, user: User) -> User:
    user.is_active = True
    user.save(update_fields=["is_active", "updated_at"])
    return user
