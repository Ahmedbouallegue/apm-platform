from rest_framework.permissions import BasePermission

from apps.accounts.roles import can_manage_users, can_write_users, is_admin_dsi


class IsAdminOrDSI(BasePermission):
    """Full access for Administrateur DSI (patrimoine)."""

    def has_permission(self, request, view) -> bool:
        return is_admin_dsi(request.user)


class CanManageUsers(BasePermission):
    """Administrateur : liste et consultation des utilisateurs."""

    def has_permission(self, request, view) -> bool:
        return can_manage_users(request.user)


class CanWriteUsers(BasePermission):
    """Administrateur : création / modification des utilisateurs."""

    def has_permission(self, request, view) -> bool:
        return can_write_users(request.user)
