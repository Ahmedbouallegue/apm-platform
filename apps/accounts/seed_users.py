"""Jeux d'utilisateurs par défaut Topnet APM (admin / dsi / system)."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model

from apps.accounts.services.users import user_create

User = get_user_model()


@dataclass(frozen=True)
class UserSeedSpec:
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    password: str
    is_staff: bool = False
    department: str = "DSI"
    phone: str = "+216 71 000 000"


DEFAULT_USER_SPECS: tuple[UserSeedSpec, ...] = (
    UserSeedSpec(
        username="admin",
        email="admin@topnet.tn",
        first_name="Admin",
        last_name="Topnet",
        role=User.Role.ADMIN,
        password="Admin123!",
        is_staff=True,
    ),
    UserSeedSpec(
        username="achref",
        email="achref@topnet.tn",
        first_name="Achref",
        last_name="Khelifi",
        role=User.Role.DSI,
        password="Dsi12345!",
        is_staff=True,
    ),
    UserSeedSpec(
        username="ines",
        email="ines@topnet.tn",
        first_name="Ines",
        last_name="Trabelsi",
        role=User.Role.DSI,
        password="Dsi12345!",
        is_staff=True,
    ),
    UserSeedSpec(
        username="system",
        email="system@topnet.tn",
        first_name="Karim",
        last_name="Mansour",
        role=User.Role.SYSTEM,
        password="System123!",
        is_staff=False,
    ),
)


def seed_default_users() -> dict[str, User]:
    """Crée les comptes par défaut (échoue si un username existe déjà)."""
    users: dict[str, User] = {}
    for spec in DEFAULT_USER_SPECS:
        user = user_create(
            username=spec.username,
            email=spec.email,
            password=spec.password,
            first_name=spec.first_name,
            last_name=spec.last_name,
            role=spec.role,
            phone=spec.phone,
            department=spec.department,
            is_staff=spec.is_staff or spec.role in {User.Role.ADMIN, User.Role.DSI},
            is_active=True,
        )
        users[spec.username] = user
    return users


def format_user_credentials() -> list[str]:
    lines = []
    for spec in DEFAULT_USER_SPECS:
        lines.append(f"  {spec.username} / {spec.password} ({spec.role})")
    return lines
