"""Rôles APM — acteurs métier et droits associés.

Acteurs :
  - Administrateur       → admin   (gestion utilisateurs et rôles uniquement)
  - Administrateur DSI   → dsi     (tout le patrimoine, sauf utilisateurs/rôles)
  - Administrateur Système → system (environnements et serveurs uniquement)
"""

from __future__ import annotations

from apps.accounts.models import User

PATRIMOINE_READ_ROLES = frozenset({User.Role.DSI})
INFRA_READ_ROLES = frozenset({User.Role.DSI, User.Role.SYSTEM})
PATRIMOINE_WRITE_ROLES = frozenset({User.Role.DSI})
INFRA_WRITE_ROLES = frozenset({User.Role.DSI, User.Role.SYSTEM})

ROLE_DESCRIPTIONS = {
    User.Role.ADMIN: (
        "Administrateur — gestion des utilisateurs et des rôles "
        "(création, modification, import/export CSV)."
    ),
    User.Role.DSI: (
        "Administrateur DSI — gestion complète du patrimoine applicatif "
        "(applications, SSL, domaines, contrats, incidents, paramètres). "
        "Pas d'accès à la gestion des utilisateurs."
    ),
    User.Role.SYSTEM: (
        "Administrateur Système — gestion des environnements et serveurs "
        "(infrastructure), consultation du monitoring."
    ),
}


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def _superuser_bypass(user) -> bool:
    return _authenticated(user) and user.is_superuser


def is_platform_admin(user) -> bool:
    """Compte Administrateur (gestion utilisateurs / rôles)."""
    if not _authenticated(user):
        return False
    return _superuser_bypass(user) or user.role == User.Role.ADMIN


def is_admin_dsi(user) -> bool:
    """Compte Administrateur DSI (patrimoine complet, pas utilisateurs)."""
    if not _authenticated(user):
        return False
    return _superuser_bypass(user) or user.role == User.Role.DSI


def is_admin_system(user) -> bool:
    """Compte Administrateur Système (environnements / serveurs)."""
    if not _authenticated(user):
        return False
    return user.role == User.Role.SYSTEM


def can_manage_users(user) -> bool:
    """Liste et export utilisateurs : Administrateur uniquement."""
    return is_platform_admin(user)


def can_write_users(user) -> bool:
    """Création / édition / import CSV utilisateurs : Administrateur uniquement."""
    return is_platform_admin(user)


def can_read_patrimoine(user) -> bool:
    """Consultation catalogue SI, ressources, supervision (hors infra dédiée)."""
    if not _authenticated(user):
        return False
    if _superuser_bypass(user):
        return True
    return user.role in PATRIMOINE_READ_ROLES


def can_read_infrastructure(user) -> bool:
    """Consultation environnements et serveurs."""
    if not _authenticated(user):
        return False
    if _superuser_bypass(user):
        return True
    return user.role in INFRA_READ_ROLES


def can_write_patrimoine(user) -> bool:
    """CRUD applications, SSL, domaines, contrats, incidents, etc."""
    if not _authenticated(user):
        return False
    if _superuser_bypass(user):
        return True
    return user.role in PATRIMOINE_WRITE_ROLES


def can_write_infrastructure(user) -> bool:
    """CRUD environnements et serveurs."""
    if not _authenticated(user):
        return False
    if _superuser_bypass(user):
        return True
    return user.role in INFRA_WRITE_ROLES


def can_configure_platform(user) -> bool:
    """Paramètres globaux (seuils d'alerte, etc.)."""
    return is_admin_dsi(user)


def can_read(user) -> bool:
    """Accès général à la plateforme (au moins une section métier)."""
    if not _authenticated(user):
        return False
    return (
        can_read_patrimoine(user)
        or can_read_infrastructure(user)
        or can_manage_users(user)
    )
