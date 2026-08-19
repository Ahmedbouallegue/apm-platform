"""Rôles APM — acteurs métier et droits associés.

Acteurs (diagramme) :
  - Administrateur DSI  → admin, dsi
  - Équipe DSI / Technicien → manager
  - Lecteur (consultation) → viewer
  - Système automatique → Celery (hors comptes utilisateurs)

Règle forte : un compte avec le rôle Lecteur n’a jamais de droits
d’écriture patrimoine / utilisateurs / paramètres, même s’il est
marqué is_superuser (erreur de configuration).
"""

from __future__ import annotations

from apps.accounts.models import User

ADMIN_DSI_ROLES = frozenset({User.Role.ADMIN, User.Role.DSI})
TECH_ROLES = frozenset({User.Role.MANAGER})
WRITE_ROLES = frozenset({User.Role.ADMIN, User.Role.DSI, User.Role.MANAGER})
READ_ROLES = frozenset(
    {User.Role.ADMIN, User.Role.DSI, User.Role.MANAGER, User.Role.VIEWER}
)

ROLE_DESCRIPTIONS = {
    User.Role.ADMIN: (
        "Administrateur DSI — gère les utilisateurs, les rôles, "
        "les paramètres globaux et les imports/exports."
    ),
    User.Role.DSI: (
        "Administrateur DSI — mêmes droits que l’administrateur "
        "(utilisateurs, paramètres, patrimoine)."
    ),
    User.Role.MANAGER: (
        "Équipe DSI / Technicien — CRUD patrimoine (applications, "
        "environnements, SSL, domaines, contrats, documentation), "
        "tableaux de bord et KPI. Pas de gestion des comptes."
    ),
    User.Role.VIEWER: (
        "Lecteur — consultation seule du patrimoine et des indicateurs."
    ),
}


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def is_viewer(user) -> bool:
    return _authenticated(user) and user.role == User.Role.VIEWER


def is_admin_dsi(user) -> bool:
    if not _authenticated(user) or is_viewer(user):
        return False
    return user.is_superuser or user.role in ADMIN_DSI_ROLES


def can_manage_users(user) -> bool:
    """Liste utilisateurs : Admin DSI + Technicien (lecture)."""
    if not _authenticated(user) or is_viewer(user):
        return False
    return user.is_superuser or user.role in WRITE_ROLES


def can_write_users(user) -> bool:
    """Création / édition / import CSV utilisateurs : Admin DSI uniquement."""
    return is_admin_dsi(user)


def can_write_patrimoine(user) -> bool:
    """CRUD applications, SSL, domaines, contrats, etc."""
    if not _authenticated(user) or is_viewer(user):
        return False
    return user.is_superuser or user.role in WRITE_ROLES


def can_configure_platform(user) -> bool:
    """Paramètres globaux (seuils d’alerte, etc.)."""
    return is_admin_dsi(user)


def can_read(user) -> bool:
    return _authenticated(user) and (
        user.is_superuser or user.role in READ_ROLES
    )
