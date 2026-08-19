"""Permissions transverses (docs API, médias, métriques)."""

from rest_framework.permissions import BasePermission

from apps.accounts.roles import can_read, is_admin_dsi


class IsAdminDSI(BasePermission):
    """Admin / DSI uniquement (API)."""

    def has_permission(self, request, view) -> bool:
        return is_admin_dsi(request.user)


class CanReadAuthenticated(BasePermission):
    """Utilisateur authentifié avec droit de lecture patrimoine."""

    def has_permission(self, request, view) -> bool:
        return can_read(request.user)
